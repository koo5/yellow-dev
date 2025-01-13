#!/usr/bin/env python3

import sys

host = sys.argv[1]

print(f"""

CREATE USER IF NOT EXISTS username IDENTIFIED BY 'password';
CREATE DATABASE IF NOT EXISTS yellow;
GRANT ALL ON yellow.* TO username;

CREATE USER  IF NOT EXISTS 'yellow_module_org_libersoft_messages' IDENTIFIED BY 'password';
CREATE DATABASE  IF NOT EXISTS yellow_module_org_libersoft_messages;
GRANT ALL ON yellow_module_org_libersoft_messages.* TO 'yellow_module_org_libersoft_messages';

USE yellow;
CREATE TABLE IF NOT EXISTS admins (id INT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(32) NOT NULL UNIQUE, password VARCHAR(255) NOT NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS admins_logins (id INT PRIMARY KEY AUTO_INCREMENT, id_admins INT, session VARCHAR(128) NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_admins) REFERENCES admins(id));
CREATE TABLE IF NOT EXISTS admins_sessions (id INT PRIMARY KEY AUTO_INCREMENT, id_admins INT, session VARCHAR(255) NOT NULL UNIQUE, last TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_admins) REFERENCES admins(id));
CREATE TABLE IF NOT EXISTS domains (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL UNIQUE, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS users (id INT PRIMARY KEY AUTO_INCREMENT, username VARCHAR(64) NOT NULL, id_domains INT, visible_name VARCHAR(255) NULL, password VARCHAR(255) NOT NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_domains) REFERENCES domains(id), UNIQUE (username, id_domains));
CREATE TABLE IF NOT EXISTS users_logins (id INT PRIMARY KEY AUTO_INCREMENT, id_users INT, session VARCHAR(128) NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_users) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS users_sessions (id INT PRIMARY KEY AUTO_INCREMENT, id_users INT, session VARCHAR(255) NOT NULL UNIQUE, last TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY (id_users) REFERENCES users(id));
CREATE TABLE IF NOT EXISTS modules (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(255) NOT NULL UNIQUE, connection_string VARCHAR(255) NOT NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE IF NOT EXISTS logs (id INT PRIMARY KEY AUTO_INCREMENT, level INT NOT NULL, topic TEXT NULL, message TEXT NULL, json JSON NULL, created TIMESTAMP DEFAULT CURRENT_TIMESTAMP);

USE yellow_module_org_libersoft_messages;
CREATE TABLE IF NOT EXISTS messages (id INT PRIMARY KEY AUTO_INCREMENT, id_users INT, uid VARCHAR(255) NOT NULL, address_from VARCHAR(255) NOT NULL, address_to VARCHAR(255) NOT NULL, message TEXT NOT NULL, format VARCHAR(16) NOT NULL DEFAULT "plaintext", seen TIMESTAMP NULL DEFAULT NULL, created TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP);

USE yellow;
INSERT INTO admins (username, password) VALUES ('admin', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');
INSERT INTO modules (name, connection_string) VALUES ('org.libersoft.messages', 'ws://localhost:25001/');
INSERT INTO domains (name) VALUES ('{host}');

INSERT INTO users (username, id_domains, visible_name, password) VALUES ('user1', (SELECT id FROM domains WHERE name = '{host}'), 'user1@{host}', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');
INSERT INTO users (username, id_domains, visible_name, password) VALUES ('user2', (SELECT id FROM domains WHERE name = '{host}'), 'user2@{host}', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');
INSERT INTO users (username, id_domains, visible_name, password) VALUES ('user3', (SELECT id FROM domains WHERE name = '{host}'), 'user3@{host}', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');
INSERT INTO users (username, id_domains, visible_name, password) VALUES ('user4', (SELECT id FROM domains WHERE name = '{host}'), 'user4@{host}', '$argon2id$v=19$m=65536,t=20,p=1$Vmb9bCJSHUOJDiS+amdMkzxTljfkanX0JKsYecdBCkQ$slQjytnGeh4/ScqmXOJ6mjjfdmu/9eVSd6dV032nrm8');

INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (1, 2, '0.b09dmbtebth0.utiw7sn3k9f0.0o0g0hg9eed0.7rgwhndqm9q', 'user2@{host}', 'user1@{host}', 'ABC', '2024-10-26 23:29:33', '2024-10-26 23:21:15');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (2, 1, '0.b09dmbtebth0.utiw7sn3k9f0.0o0g0hg9eed0.7rgwhndqm9q', 'user2@{host}', 'user1@{host}', 'ABC', '2024-10-26 23:29:33', '2024-10-26 23:21:16');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (3, 3, '0.b4j19b5zex70.a72knqivskn0.kr3vzg48xfn0.m08j39zy1or', 'user3@{host}', 'user1@{host}', 'hello fron user3', '2024-10-26 23:29:08', '2024-10-26 23:28:29');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (4, 1, '0.b4j19b5zex70.a72knqivskn0.kr3vzg48xfn0.m08j39zy1or', 'user3@{host}', 'user1@{host}', 'hello fron user3', '2024-10-26 23:29:08', '2024-10-26 23:28:29');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (5, 1, '0.nm8szdn6l3l0.23osj3k5imw0.7htrja5b4380.jc7x8267fo', 'user1@{host}', 'user3@{host}', 'good to see you user3', null, '2024-10-26 23:29:20');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (6, 3, '0.nm8szdn6l3l0.23osj3k5imw0.7htrja5b4380.jc7x8267fo', 'user1@{host}', 'user3@{host}', 'good to see you user3', null, '2024-10-26 23:29:20');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (7, 1, '0.4pvy92zmo2a0.907pal1cgf50.4zionrttiri0.p3uny72ata', 'user1@{host}', 'user2@{host}', 'RARARARARERERERERRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRH!', null, '2024-10-26 23:30:03');
INSERT INTO yellow_module_org_libersoft_messages.messages (id, id_users, uid, address_from, address_to, message, seen, created) VALUES (8, 2, '0.4pvy92zmo2a0.907pal1cgf50.4zionrttiri0.p3uny72ata', 'user1@{host}', 'user2@{host}', 'RARARARARERERERERRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRRH!', null, '2024-10-26 23:30:03');

""")


