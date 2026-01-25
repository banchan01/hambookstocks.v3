from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.dependencies.db import get_db_session
from app.models.DB_user_models import User
from app.models.DB_mystocks_models import MyStocks
from app.models.DB_trade_models import TradeStocks
from app.models.DB_Market_stocks_models import MarketStocks
from app.models.DB_User_stocks_models import UserStocks
from app.models.parameter_models import stock_to_buy_and_sell
from app.dependencies.redis_db import get_redis
from app.services.redis_service import RedisService
from sqlmodel import select

router = APIRouter(prefix="/trade")

# 주식 가격변동계수
alpha = 0.1


@router.post("/buy_request")  # req: 수량, 금액, 주식 코드,
async def buy_stock(
    req: stock_to_buy_and_sell,
    db: Session = Depends(get_db_session),
    authorization: str = Header(None),
    redis_db=Depends(get_redis),
    redis_service: RedisService = Depends(),
):
    if req.stock_price is None:
        raise HTTPException(status_code=400, detail="주식 가격이 필요합니다.")

    if not authorization:
        raise HTTPException(status_code=401, detail="로그인하셔야 합니다.")

    token = authorization.split(" ")[1]

    if not (login_id := await redis_db.get(token)):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    transaction_occurred = False
    trade_transactions = []
    """
    돈 있는지 확인 / 돈 없으면 구매 불가능
    """
    user = db.exec(select(User).where(User.login_id == login_id).with_for_update()).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    if user.balance < req.quantity * req.stock_price:
        raise HTTPException(status_code=400, detail="잔액이 부족합니다.")

    """
    판매 중인 주문 찾기
    """
    trade_info_list = db.exec(
        select(TradeStocks)
        .where(TradeStocks.stock_name == req.stock_name, TradeStocks.is_buy == False)
        .order_by(TradeStocks.id)
        .with_for_update()
    ).all()
    
    trade_info = trade_info_list[0] if trade_info_list else None
    
    seller = None

    if trade_info_list:  # 팔려는 사람(매도 주문)이 있다면 거래 시작!
        remaining_quantity = req.quantity
        
        for trade_info in trade_info_list:
            if remaining_quantity <= 0:
                break
                
            if trade_info.quantity > remaining_quantity:
                trade_amount = remaining_quantity
                trade_info.quantity -= remaining_quantity
                remaining_quantity = 0
            else:
                trade_amount = trade_info.quantity
                remaining_quantity -= trade_info.quantity
                db.delete(trade_info) # 판매 물량 소진 시 삭제

            transaction_occurred = True
            trade_transactions.append((trade_info.login_id, trade_amount))

        # 만약 다 못 샀는데 판매 물량이 끝났다면, 남은 만큼 매수 주문 등록
        if remaining_quantity > 0:
            db.add(TradeStocks(login_id=login_id, stock_name=req.stock_name, quantity=remaining_quantity, is_buy=True))

    else:  # 팔려는 사람이 아예 없으면 내 주문을 게시판에 올림
        # 기존에 내가 올린 매수 주문이 있는지 확인
        my_existing_order = db.exec(select(TradeStocks).where(
            TradeStocks.login_id == login_id, 
            TradeStocks.stock_name == req.stock_name, 
            TradeStocks.is_buy == True
        )).first()
        
        if my_existing_order:
            my_existing_order.quantity += req.quantity
        else:
            db.add(TradeStocks(login_id=login_id, stock_name=req.stock_name, quantity=req.quantity, is_buy=True))

    """
    구매한 user balance 차감, Mystocks 에 보유주식 추가
    판매한 user balance 증가, Mystocks 에 보유주식 감소
    """
    if transaction_occurred and trade_transactions:
        user.balance -= sum(
            trade_amount * req.stock_price for _, trade_amount in trade_transactions
        )  # 구매자 balance 차감

        # 판매자 balance , 주식 수량 감소
        for seller_id, trade_amount in trade_transactions:
            seller = db.exec(select(User).where(User.login_id == seller_id)).first()
            if seller:
                seller.balance += trade_amount * req.stock_price  # 판매자 balance 증가

        # 구매자의 보유 주식 업데이트
        buyer_stock = db.exec(
            select(MyStocks).where(
                MyStocks.login_id == login_id, MyStocks.stock_name == req.stock_name
            )
        ).first()
        if not buyer_stock:
            buyer_stock = MyStocks(
                login_id=login_id,
                stock_name=req.stock_name,
                quantity=sum(trade_amount for _, trade_amount in trade_transactions),
            )
            db.add(buyer_stock)
        else:
            buyer_stock.quantity += sum(
                trade_amount for _, trade_amount in trade_transactions
            )
            db.add(buyer_stock) # 명시적 추가 (Dirty checking 보장)

    """
    tradestocks 에 is_buy 인것과 quantity 를 불러온걸 활용해서 가격변동
    """
    new_stock_price = req.stock_price + (req.quantity * alpha)


    updated_stock_for_price = db.exec(
        select(UserStocks).where(UserStocks.stock_name == req.stock_name)
    ).first()

    if not updated_stock_for_price:
        updated_stock_for_price = db.exec(
            select(MarketStocks).where(MarketStocks.stock_name == req.stock_name)
        ).first()

    updated_stock_for_price.stock_price = new_stock_price
    db.commit()
    """
    변동된 가격을 redis에 저장함
    """
    await redis_service.update_stock(redis_db, req.stock_name, new_stock_price)

    return {"msg": "매수요청 완료"}


@router.post("/sell_request")
async def sell_order(
    req: stock_to_buy_and_sell,
    db=Depends(get_db_session),
    authorization: str = Header(None),
    redis_db=Depends(get_redis),
    redis_service: RedisService = Depends(),
):
    if req.stock_price is None:
        raise HTTPException(status_code=400, detail="주식 가격이 필요합니다.")
    """토큰인증"""

    if not authorization:
        raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다.")
    token = authorization.split(" ")[1]  # "Bearer <토큰>"에서 토큰만 추출

    if not (login_id := await redis_db.get(token)):
        raise HTTPException(status_code=401, detail="유효하지 않은 토큰입니다")

    transaction_occurred = False
    trade_transactions = []

    """
    주식 있는지 확인 / 주식 없으면 매도 불가능
    """
    user = db.exec(select(User).where(User.login_id == login_id).with_for_update()).first()
    if not user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    seller_stock = db.exec(
        select(MyStocks).where(
            MyStocks.login_id == login_id, MyStocks.stock_name == req.stock_name
        ).with_for_update()
    ).first()
    if not seller_stock:
        raise HTTPException(status_code=404, detail="보유주식을 찾을 수 없습니다.")

    if seller_stock.quantity < req.quantity:
        raise HTTPException(status_code=400, detail="보유주식 수량이 부족합니다.")

    """
    buy_req 올라온거 trade_stocks에서 찾고, 찾는 수량보다 적게 있으면.. 있는 만큼 판매하고, 없는 만큼 sell_req 를 tradestocks에 올린다
    """
    # 팔러 왔으니 매수 주문만 찾아야 함
    trade_info_list = db.exec(
        select(TradeStocks)
        .where(TradeStocks.stock_name == req.stock_name, TradeStocks.is_buy == True)
        .order_by(TradeStocks.id)
        .with_for_update()
    ).all()
    
    # 첫 번째 매수 물량 확인용
    trade_info = trade_info_list[0] if trade_info_list else None

    if trade_info_list:  # 사겠다는 사람(매수 주문)이 있다면 거래 시작!
        remaining_quantity = req.quantity
        
        for trade_info in trade_info_list:
            if remaining_quantity <= 0:
                break
                
            if trade_info.quantity > remaining_quantity:
                trade_amount = remaining_quantity
                trade_info.quantity -= remaining_quantity
                remaining_quantity = 0
            else:
                trade_amount = trade_info.quantity
                remaining_quantity -= trade_info.quantity
                db.delete(trade_info) # 매수 주문 소진 시 삭제

            transaction_occurred = True
            trade_transactions.append((trade_info.login_id, trade_amount)) # (구매자ID, 거래수량)

        # 시장의 매수 물량을 다 채워줬는데도 내 주식이 남았다면, 남은 만큼 판매 주문 등록
        if remaining_quantity > 0:
            db.add(TradeStocks(login_id=login_id, stock_name=req.stock_name, quantity=remaining_quantity, is_buy=False))

    else:  # 사겠다는 사람이 아무도 없으면 내 판매 주문을 게시판에 올림
        # 기존에 내가 올린 판매 주문이 있는지 확인
        my_existing_order = db.exec(select(TradeStocks).where(
            TradeStocks.login_id == login_id, 
            TradeStocks.stock_name == req.stock_name, 
            TradeStocks.is_buy == False
        )).first()
        
        if my_existing_order:
            my_existing_order.quantity += req.quantity
        else:
            db.add(TradeStocks(login_id=login_id, stock_name=req.stock_name, quantity=req.quantity, is_buy=False))

    # 판매 주문을 올렸거나 거래가 성사되었으므로, 내 보유 주식에서 해당 수량만큼 차감해야 함
    seller_stock.quantity -= req.quantity
    
    db.commit()

    """
    구매한 user balance 차감, Mystocks 에 보유주식 추가
    판매한 user balance 증가, Mystocks 에 보유주식 감소
    """
    if transaction_occurred and trade_transactions:
        seller = db.exec(select(User).where(User.login_id == login_id)).first()

        # 판매자 balance 증가
        seller.balance += sum(
            trade_amount * req.stock_price for _, trade_amount in trade_transactions
        )

        # 여러 구매자의 balance 및 MyStocks 업데이트
        for buyer_id, trade_amount in trade_transactions:
            buyer = db.exec(select(User).where(User.login_id == buyer_id)).first()
            if buyer:
                buyer.balance -= trade_amount * req.stock_price  # 구매자 balance 차감

                # 구매자의 보유 주식 업데이트
                buyer_stock = db.exec(
                    select(MyStocks).where(
                        MyStocks.login_id == buyer_id,
                        MyStocks.stock_name == req.stock_name,
                    )
                ).first()

                if not buyer_stock:
                    buyer_stock = MyStocks(
                        login_id=buyer_id,
                        stock_name=req.stock_name,
                        quantity=trade_amount,
                    )
                    db.add(buyer_stock)
                else:
                    buyer_stock.quantity += trade_amount

        if seller_stock:
            pass

        db.commit()

    """
    tradestocks 에 is_buy 인것과 quantity 를 불러온걸 활용해서 가격변동
    """
    new_stock_price = max(1, req.stock_price - (req.quantity * alpha))
    print(f"DEBUG: Sell Price Change -> Old: {req.stock_price}, New: {new_stock_price}")

    updated_stock_for_price = db.exec(
        select(UserStocks).where(UserStocks.stock_name == req.stock_name)
    ).first()

    if not updated_stock_for_price:
        updated_stock_for_price = db.exec(
            select(MarketStocks).where(MarketStocks.stock_name == req.stock_name)
        ).first()

    updated_stock_for_price.stock_price = new_stock_price
    db.commit()

    """
    변동된 가격을 redis에 저장함
    """
    await redis_service.update_stock(redis_db, req.stock_name, new_stock_price)

    return {"msg": "매도 요청 완료"}
