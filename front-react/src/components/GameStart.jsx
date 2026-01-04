import '../styles/GameStart.css';
import { get_news } from '../services/NewsService';
import { useState, useEffect, useRef } from 'react';
import { chatService } from '../services/ChatService';

export default function GameStart({ onGameStart }) {
  const [news, setNews] = useState([]);
  const [isChatOpen, setIsChatOpen] = useState(() => {
    const savedState = localStorage.getItem('isChatOpen');
    return savedState !== null ? savedState === 'true' : true; // 기본값 true
  }); 

  // 채팅 상태 변경 시 로컬 스토리지 저장
  const toggleChat = () => {
    setIsChatOpen((prev) => {
      const newState = !prev;
      localStorage.setItem('isChatOpen', newState);
      return newState;
    });
  };
  const [inputMessage, setInputMessage] = useState('');
  const [messages, setMessages] = useState(
    JSON.parse(sessionStorage.getItem('chatMessages')) || [],
  );

  const newsRef = useRef(null); // 뉴스 섹션 참조

  const scrollToNews = () => {
    newsRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const chatMessagesRef = useRef(null);
  useEffect(() => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  }, [messages]);

  useEffect(() => {
    chatService.connect();

    chatService.ws.onmessage = (event) => {
      setMessages((prev) => {
        const newMessages = [...prev, event.data];
        sessionStorage.setItem('chatMessages', JSON.stringify(newMessages));
        return newMessages;
      });
    };

    return () => {
      chatService.disconnect();
    };
  }, []);

  // 메시지 전송 함수
  const sendMessage = () => {
    if (inputMessage.trim()) {
      chatService.sendMessage(inputMessage);
      setInputMessage('');
    }
  };

  useEffect(() => {
    const getNews = async () => {
      try {
        const newsData = await get_news();
        setNews(newsData.summarized_news);
      } catch (error) {
        console.error('뉴스 가져오기 실패', error);
      }
    };
    getNews();
  }, []);

  const [chatSize, setChatSize] = useState({ width: 400, height: 600 });

  const handleResizeMouseDown = (e) => {
    e.preventDefault();
    const startX = e.clientX;
    const startY = e.clientY;
    const startWidth = chatSize.width;
    const startHeight = chatSize.height;

    const onMouseMove = (moveEvent) => {
      const deltaX = moveEvent.clientX - startX;
      const deltaY = moveEvent.clientY - startY;
      setChatSize({
        width: Math.max(320, startWidth + deltaX),
        height: Math.max(300, startHeight - deltaY), // 위로 드래그하면 높이 증가
      });
    };

    const onMouseUp = () => {
      document.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseup', onMouseUp);
    };

    document.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseup', onMouseUp);
  };

  const handleGameStart = () => {
    const token = localStorage.getItem('token');
    if (!token) {
      alert('로그인이 필요한 서비스입니다.');
      return;
    }
    onGameStart();
  };

  return (
    <div className="game-start-container">
      {/* Hero Section: 타이틀 및 시작 버튼 */}
      <div className="hero-section">
        <h1 className="main-title">햄북스딱스에 오신걸 환영합니다!</h1>
        <p className="sub-title">쉽고 재미있는 실시간 모의 주식 투자 서비스를 경험해보세요.</p>
        <button className="start-button" onClick={handleGameStart}>
          게임 시작
        </button>
      </div>

      {/* Content Section: 뉴스 (메인 컨텐츠) */}
      <div className="content-section" ref={newsRef}>
        <div className="scroll-hint-news" onClick={scrollToNews}>
          <p>최신 뉴스 확인하기</p>
          <span className="arrow-down">↓</span>
        </div>
        <div className="news-section">
          <h2>최신 뉴스</h2>
          <div className="news-list">
            {news.slice(0, 5).map((newsItem, index) => (
              <div key={index} className="news-item">
                <h3>{newsItem.제목}</h3>
                <p>{newsItem.본문}</p>
                <a href={newsItem.링크} target="_blank" rel="noopener noreferrer">
                  원문 보기
                </a>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Chat Section: 플로팅 팝업 스타일 */}
      <div 
        className={`chat-section floating-chat ${isChatOpen ? 'open' : 'closed'}`}
        style={isChatOpen ? { width: chatSize.width, height: chatSize.height } : {}}
      >
        {isChatOpen && <div className="resize-handle" onMouseDown={handleResizeMouseDown}></div>}
        
        <div className="chat-header" onClick={toggleChat}>
          <h2>
            STOCK TALK
            <span className="toggle-icon">{isChatOpen ? '▼' : '▲'}</span>
          </h2>
        </div>
        {isChatOpen && (
          <>
            <div className="chat-messages" ref={chatMessagesRef}>
              {messages.map((msg, index) => {
                try {
                  const messageObj =
                    typeof msg === 'string' ? JSON.parse(msg.split(' says: ')[1]) : msg;
                  const username = msg.split(' says: ')[0].replace('Client #', '');
                  const content = messageObj.content;

                  const loginId = localStorage.getItem('login_id');
                  let currentUser = loginId || chatService.guestId;

                  if (loginId && username.startsWith('guest_')) {
                    currentUser = chatService.guestId;
                  }

                  const isMyMessage = username === currentUser;
                  return (
                    <div
                      key={index}
                      className={`chat-message ${isMyMessage ? 'my-message' : 'other-message'}`}
                    >
                      <span className="username">{username}</span>
                      <span className="separator">: </span>
                      <span className="content">{content}</span>
                    </div>
                  );
                } catch (error) {
                  return null;
                }
              })}
            </div>
            <div className="chat-input">
              <input
                type="text"
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                placeholder="메시지를 입력하세요"
              />
              <button onClick={sendMessage}>전송</button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
