use education;

CREATE TABLE users (
    user_id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    role VARCHAR(20) DEFAULT 'user',  -- user/admin
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- 投票表
CREATE TABLE polls (
    poll_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    create_user_id INT,
    start_time DATETIME,
    end_time DATETIME,
    status VARCHAR(20) DEFAULT 'active',  -- active/closed
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (create_user_id) REFERENCES users(user_id)
);

-- 投票选项表
CREATE TABLE poll_options (
    option_id INT PRIMARY KEY AUTO_INCREMENT,
    poll_id INT,
    option_text VARCHAR(200) NOT NULL,
    votes_count INT DEFAULT 0,
    FOREIGN KEY (poll_id) REFERENCES polls(poll_id)
);

-- 用户投票记录表
CREATE TABLE user_votes (
    vote_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    poll_id INT,
    option_id INT,
    vote_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    FOREIGN KEY (poll_id) REFERENCES polls(poll_id),
    FOREIGN KEY (option_id) REFERENCES poll_options(option_id)
);

-- 决策表
CREATE TABLE decisions (
    decision_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    create_user_id INT,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/approved/rejected
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (create_user_id) REFERENCES users(user_id)
);

-- 资讯表
CREATE TABLE news (
    news_id INT PRIMARY KEY AUTO_INCREMENT,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    author_id INT,
    category VARCHAR(50),
    views INT DEFAULT 0,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (author_id) REFERENCES users(user_id)
);