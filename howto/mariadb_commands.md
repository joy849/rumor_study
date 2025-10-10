# MariaDB 명령어 정리

## MariaDB 서비스 관리
```bash
# MariaDB 상태 확인
systemctl status mariadb

# MariaDB 시작
sudo systemctl start mariadb

# MariaDB 중지
sudo systemctl stop mariadb

# MariaDB 재시작
sudo systemctl restart mariadb
```

## 데이터베이스 조회
```bash
# 모든 데이터베이스 보기
mysql -u dtuser -p1234 -e "SHOW DATABASES;"

# root 계정으로 모든 데이터베이스 보기
mysql -u root -e "SHOW DATABASES;"
```

## 테이블 조회
```bash
# stock5_db의 모든 테이블 보기 (dtuser)
mysql -u dtuser -p1234 stock5_db -e "SHOW TABLES;"

# stock5_db의 모든 테이블 보기 (root)
mysql -u root stock5_db -e "SHOW TABLES;"
```

## 테이블 구조 확인
```bash
# ausers 테이블 구조 보기
mysql -u root stock5_db -e "DESCRIBE ausers;"

# user_profiles 테이블 구조 보기
mysql -u root stock5_db -e "DESCRIBE user_profiles;"

# 테이블 생성 쿼리 확인
mysql -u root stock5_db -e "SHOW CREATE TABLE ausers\G"
```

## 데이터 조회
```bash
# ausers 테이블 전체 데이터 조회
mysql -u root stock5_db -e "SELECT * FROM ausers;"

# user_profiles 테이블 전체 데이터 조회
mysql -u root stock5_db -e "SELECT * FROM user_profiles;"

# 특정 조건으로 조회
mysql -u root stock5_db -e "SELECT * FROM ausers WHERE role='USER';"

# 개수 확인
mysql -u root stock5_db -e "SELECT COUNT(*) FROM ausers;"

# 최근 데이터 조회
mysql -u root stock5_db -e "SELECT * FROM ausers ORDER BY created_at DESC LIMIT 5;"
```

## 데이터 삽입/수정/삭제
```bash
# 데이터 삽입
mysql -u root stock5_db -e "INSERT INTO ausers (email, name, password, role, created_at) VALUES ('test@test.com', 'Test User', 'password123', 'USER', NOW());"

# 데이터 수정
mysql -u root stock5_db -e "UPDATE ausers SET name='Updated Name' WHERE email='test@test.com';"

# 데이터 삭제
mysql -u root stock5_db -e "DELETE FROM ausers WHERE email='test@test.com';"
```

## 사용자 및 권한 관리
```bash
# 모든 사용자 보기
mysql -u root -e "SELECT User, Host FROM mysql.user;"

# 특정 사용자 권한 확인
mysql -u root -e "SHOW GRANTS FOR 'dtuser'@'localhost';"

# 새 사용자 생성
mysql -u root -e "CREATE USER 'newuser'@'localhost' IDENTIFIED BY 'password';"

# 권한 부여
mysql -u root -e "GRANT ALL PRIVILEGES ON stock5_db.* TO 'newuser'@'localhost';"

# 권한 적용
mysql -u root -e "FLUSH PRIVILEGES;"

# 사용자 삭제
mysql -u root -e "DROP USER 'newuser'@'localhost';"
```

## 데이터베이스 관리
```bash
# 새 데이터베이스 생성
mysql -u root -e "CREATE DATABASE new_db;"

# 데이터베이스 삭제
mysql -u root -e "DROP DATABASE new_db;"

# 데이터베이스 크기 확인
mysql -u root -e "SELECT table_schema AS 'Database', ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)' FROM information_schema.TABLES GROUP BY table_schema;"
```

## 테이블 관리
```bash
# 테이블 생성
mysql -u root stock5_db -e "CREATE TABLE test_table (id INT AUTO_INCREMENT PRIMARY KEY, name VARCHAR(100));"

# 테이블 삭제
mysql -u root stock5_db -e "DROP TABLE test_table;"

# 테이블 비우기 (구조는 유지)
mysql -u root stock5_db -e "TRUNCATE TABLE test_table;"

# 테이블 인덱스 확인
mysql -u root stock5_db -e "SHOW INDEX FROM ausers;"
```

## 백업 및 복원
```bash
# 데이터베이스 백업
mysqldump -u root stock5_db > stock5_db_backup.sql

# 특정 테이블만 백업
mysqldump -u root stock5_db ausers > ausers_backup.sql

# 데이터베이스 복원
mysql -u root stock5_db < stock5_db_backup.sql

# 새 데이터베이스에 복원
mysql -u root -e "CREATE DATABASE stock5_db_restore;"
mysql -u root stock5_db_restore < stock5_db_backup.sql
```

## 서버 상태 및 성능
```bash
# 서버 상태 확인
mysql -u root -e "SHOW STATUS;"

# 프로세스 목록 확인
mysql -u root -e "SHOW PROCESSLIST;"

# 변수 확인
mysql -u root -e "SHOW VARIABLES;"

# 특정 변수 확인
mysql -u root -e "SHOW VARIABLES LIKE 'max_connections';"

# 현재 연결 수 확인
mysql -u root -e "SHOW STATUS LIKE 'Threads_connected';"
```

## MariaDB 접속 (대화형)
```bash
# dtuser로 stock5_db 접속
mysql -u dtuser -p1234 stock5_db

# root로 접속
mysql -u root

# 접속 후 사용 가능한 명령어
SHOW DATABASES;
USE stock5_db;
SHOW TABLES;
SELECT * FROM ausers;
exit;
```
