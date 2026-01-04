# HAMBOOK STOCKS

**HAMBOOK STOCKS**는 실시간 모의 주식 투자 웹 서비스입니다.  
사용자는 가상의 자산으로 주식을 매매하고, 자신만의 주식을 상장하며, 다른 사용자들과 소통할 수 있습니다.

👉 **서비스 바로가기**: [https://hambook-stocks.me/](https://hambook-stocks.me/)

<img width="1906" height="904" alt="Hambook Stocks Screenshot" src="https://github.com/user-attachments/assets/5f5ae143-b4b1-4957-a490-ac47a919ad26" />

---

## 🎯 주요 기능

*   **실시간 거래**: 실시간 가격 변동 로직을 기반으로 매수 및 매도 주문을 체결할 수 있습니다.
*   **나만의 주식 상장**: 사용자가 직접 자신의 주식을 상장하고 거래할 수 있는 기능을 제공합니다.
*   **최신 뉴스 요약**: 매일경제 최신뉴스를 크롤링하고 AI가 요약하여 제공합니다.
*   **실시간 채팅**: 웹소켓을 이용한 채팅 기능을 통해 다른 투자자들과 정보를 교환할 수 있습니다.
*   **사용자 관리**: 회원가입, 로그인 및 자산 관리 기능을 제공합니다.

---

## 🛠 아키텍처

<img width="2726" height="1316" alt="아키텍쳐" src="https://github.com/user-attachments/assets/6a33d512-3083-4e17-a675-32d598f28f24" />
HambookStocks는 안정적인 서비스 운영을 위해 Docker 컨테이너 기반으로 설계되었으며, 각 컴포넌트는 아래와 같은 역할을 담당합니다.

<br/>

*   **Nginx**
    *   외부 요청을 받아 내부 서비스로 라우팅하는 Reverse Proxy 역할을 수행합니다.
    *   `/api` 경로는 **FastAPI** 백엔드로, 그 외 요청은 **React** 프론트엔드로 전달합니다.
*   **Docker**
    *   MySQL, Redis, Backend, Frontend 등 서비스 구동에 필요한 컴포넌트를 컨테이너로 정의하여 관리합니다.
    *   복잡한 설정 없이 `docker compose up` 로 전체 서비스 환경을 구축하고 실행할 수 있도록 합니다.
*   **FastAPI**
    *   사용자 로그인/회원가입, 주식 매수/매도 주문 체결, 실시간 데이터 처리 등 서비스의 핵심 로직을 수행합니다.
*   **React**
    *   사용자가 시세 확인, 주문, 채팅 등 서비스를 이용하는 웹 인터페이스를 제공합니다.
*   **MySQL**
    *   회원 정보, 사용자의 자산 및 보유 주식 현황, 거래 내역 등 데이터를 저장하고 관리합니다.
*   **Redis**
    *   실시간으로 변동하는 주식 시세와 뉴스 데이터를 캐싱하여 빠르게 제공하고, 로그인 세션 정보를 관리합니다.

---

## 📚 기술 스택


| 분류 | 기술 |
| :--- | :--- |
| **Frontend** | ![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black) ![Recharts](https://img.shields.io/badge/Recharts-22b5bf?style=flat-square) 
| **Backend** | ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white) ![WebSocket](https://img.shields.io/badge/WebSocket-1E1F1C?style=flat-square) |
| **Database** | ![MySQL](https://img.shields.io/badge/MySQL-4479A1?style=flat-square&logo=mysql&logoColor=white) ![Redis](https://img.shields.io/badge/Redis-DC382D?style=flat-square&logo=redis&logoColor=white) |
| **Infra** | ![AWS EC2](https://img.shields.io/badge/AWS%20EC2-FF9900?style=flat-square&logo=amazon-aws&logoColor=white) ![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white) ![Nginx](https://img.shields.io/badge/Nginx-009639?style=flat-square&logo=nginx&logoColor=white) | ![Certbot](https://img.shields.io/badge/Certbot-003BEE?style=flat-square&logo=eff&logoColor=white) ![Let's Encrypt](https://img.shields.io/badge/Let's%20Encrypt-003A70?style=flat-square&logo=letsencrypt&logoColor=white)

---

## 🚀 실행 방법

이 프로젝트는 Docker Compose를 사용하여 간편하게 실행할 수 있습니다.


> **💡 로컬 환경 실행 시 주의사항**<br>
> 본 프로젝트의 기본 설정에는 Certbot(SSL) 설정이 포함되어 있습니다.<br>
> **로컬 환경** 에서 테스트할 경우, `docker-compose.yml`에서 Certbot 관련 설정을 주석 처리하거나 Nginx 설정을 로컬에 맞춰 수정해야 정상적으로 실행됩니다.

### 1. 사전 요구사항

프로젝트 실행을 위해서는 **Docker**와 **Docker Compose**가 시스템에 설치되어 있어야 합니다. 

### 2. 프로젝트 Clone

터미널을 열고 프로젝트 코드를 로컬 컴퓨터로 복사합니다.

```bash
git clone https://github.com/banchan01/hambookstocks.v3.git
cd hambookstocks.v3
```

### 3. 환경 변수 설정

프로젝트 실행에 필요한 비밀번호, API 키 등을 설정하기 위해 `.env` 파일이 필요합니다.  
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래 내용을 복사하여 환경에 맞게 값을 채워주세요.

> ⚠️ **주의:** `.env` 파일에는 민감한 정보가 포함되므로 외부로 유출되지 않도록 각별히 유의해야 합니다.

```ini
MYSQL_USERNAME=
MYSQL_PASSWORD=
MYSQL_HOST=                 # docker-compose mysql service 이름
MYSQL_PORT=
MYSQL_DBNAME=
REDIS_HOST=                 # docker-compose redis service 이름
GPT_KEY=                    # OpenAI API Key (뉴스 요약 기능용)
```

### 4. 도커 이미지 다운로드
`docker-compose.yml`에 정의된 도커 이미지들을 dockerhub에서 다운로드합니다.
```bash
docker compose pull
```

### 5. 서비스 실행
이미지 다운로드가 완료되면 서비스를 실행합니다.
```bash
docker compose up -d
```

### 6. 실행 확인

실행이 완료되었다면 브라우저를 열고 다음 주소에 접속하여 서비스가 정상적으로 동작하는지 확인합니다.

👉 **접속 주소**: [http://localhost](http://localhost)

---

## 👥 팀원

| 이름 | 역할 | 담당 분야 |
| :---: | :---: | :--- |
| **김민찬** | Backend | FastAPI 기반 API 개발, DB 설계, Docker 인프라 구축, AWS EC2 배포 |
| **하승원** | Frontend | React 기반 사용자 인터페이스 개발, 컴포넌트 설계 |
| **김혜빈** | Frontend | React 기반 사용자 인터페이스 개발, 컴포넌트 설계 |
| **이서진** | Backend | FastAPI 기반 API 개발, DB 설계 |

---

## 📄 라이선스

MIT License

Copyright (c) 2025 banchan_01

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
