# FinGuard - 금융 루머 검증 시스템

실시간 공시 정보와 루머 검증을 제공하는 금융 정보 서비스

## 📁 프로젝트 구조

```
rumor_study/
└── stockkkkk/                          # Spring Boot 프로젝트
    ├── src/main/
    │   ├── java/com/example/stockkkkk/
    │   │   ├── global/
    │   │   │   ├── config/             # 설정 (Security, CORS, WebMvc)
    │   │   │   └── auth/jwt/           # JWT 인증
    │   │   └── auser/                  # 사용자 도메인
    │   │
    │   └── resources/
    │       ├── application.yml         # Spring Boot 설정
    │       └── static/                 # 프론트엔드 (React 스타일 구조)
    │           ├── index.html
    │           │
    │           ├── assets/             # 전역 리소스
    │           │   ├── styles/
    │           │   │   └── global.css
    │           │   └── scripts/
    │           │       └── main.js     # 라우터, 드로어 (196줄)
    │           │
    │           ├── features/           # 기능별 모듈 (React 스타일)
    │           │   ├── home/
    │           │   │   ├── home.js
    │           │   │   └── components/
    │           │   │       ├── HomeChat.html
    │           │   │       ├── HomeChat.css
    │           │   │       └── HomeChat.js
    │           │   ├── disclosure/     # 공시 탭
    │           │   │   └── disclosure.js
    │           │   ├── rumor/          # 루머체크 탭
    │           │   │   ├── rumor.html
    │           │   │   └── rumor.js
    │           │   ├── detail/         # 루머 상세
    │           │   │   ├── detail.html
    │           │   │   └── detail.js
    │           │   └── profile/        # 프로필
    │           │       ├── profile.html
    │           │       └── profile.js
    │           │
    │           └── shared/             # 공유 컴포넌트 및 서비스
    │               ├── components/
    │               │   └── modals/
    │               │       ├── LoginModal.html
    │               │       ├── SubmitModal.html
    │               │       └── DetailModal.html
    │               └── services/       # 전역 서비스
    │                   ├── api-client.js
    │                   ├── auth-manager.js
    │                   └── modal-controller.js
    │
    ├── build.gradle                    # Gradle 빌드 설정
    └── gradlew                         # Gradle Wrapper
```

## 🛠 기술 스택

### Backend
- **Framework**: Spring Boot 3.x
- **Language**: Java 17+
- **Database**: MariaDB
- **Security**: Spring Security + JWT
- **Build Tool**: Gradle

### Frontend
- **Architecture**: Vanilla JS (React-like 폴더 구조)
- **Styling**: CSS3 (CSS Variables)
- **Router**: Hash-based SPA Router
- **Modals**: Native `<dialog>` API

### Testing
- **E2E**: Playwright

## 🚀 시작하기

### 필수 요구사항
- Java 17 이상
- MariaDB 10.x
- Node.js (Playwright 테스트용)

### 데이터베이스 설정

```sql
CREATE DATABASE stock5_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'dtuser'@'localhost' IDENTIFIED BY '1234';
GRANT ALL PRIVILEGES ON stock5_db.* TO 'dtuser'@'localhost';
FLUSH PRIVILEGES;
```

### 애플리케이션 실행

```bash
cd stockkkkk
./gradlew bootRun
```

서버가 `http://localhost:8080`에서 실행됩니다.

### 다른 환경에서 접속

```bash
# application.yml에서 설정
server:
  address: 0.0.0.0  # 모든 IP에서 접속 가능
  port: 8080
```

## 📱 주요 기능

### 1. 홈 (Home)
- 채팅 인터페이스로 금융 정보 조회
- 실시간 주가 및 공시 정보 확인

### 2. 공시 (Disclosure)
- 실시간 DART 공시 목록
- 기업별/유형별 필터링
- 검증 상태 표시

### 3. 루머체크 (Rumor)
- 루머 검증 요청
- AI 패턴 분석 예측
- 유사 사례 분석
- 커뮤니티 의견

### 4. 프로필 (Profile)
- 사용자 정보 관리
- 로그인/로그아웃
- 검증 히스토리

## 🏗 아키텍처 특징

### Frontend 모듈화
- **Feature-based 구조**: 각 기능을 독립적인 폴더로 분리
- **Shared Services**: API 클라이언트, 인증 관리자를 전역 서비스로 분리
- **Dynamic Loading**: 모달 및 뷰를 동적으로 로드하여 초기 로딩 최적화

### Backend 보안
- **JWT 기반 인증**: Access Token + Refresh Token
- **Spring Security**: 경로별 권한 관리
- **CORS 설정**: 외부 도메인 접근 제어

## 📝 주요 설정 파일

### application.yml
```yaml
spring:
  datasource:
    url: jdbc:mariadb://localhost:3306/stock5_db
    username: dtuser
    password: 1234

  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true

server:
  address: 0.0.0.0
  port: 8080
```

### SecurityConfig.java
```java
// 정적 리소스 허용
.requestMatchers("/assets/**", "/features/**", "/shared/**",
                 "/*.html", "/*.css", "/*.js").permitAll()
```

## 🔧 개발 가이드

### 새로운 Feature 추가

1. `features/` 아래 새 폴더 생성
2. HTML, CSS, JS 파일 작성
3. `index.html`에 스크립트 태그 추가
4. 필요시 라우터에 경로 추가

### 새로운 Modal 추가

1. `shared/components/modals/` 에 HTML 파일 생성
2. `modal-controller.js`에서 초기화
3. `index.html`의 모달 로더에 추가

## 🐛 알려진 이슈

- **브라우저 캐시**: 정적 리소스 변경 시 하드 리프레시 필요 (`Ctrl+Shift+R`)
- **서버 재시작**: JS 파일 수정 후 Spring Boot 서버 재시작 필요

## 📄 라이선스

이 프로젝트는 교육 목적으로 작성되었습니다.

## 👥 기여자

- Backend & Frontend Architecture
- Security & Authentication
- UI/UX Design

---

**FinGuard** - 신뢰할 수 있는 금융 정보 서비스
