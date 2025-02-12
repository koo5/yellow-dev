#!/usr/bin/env python3

import sys

host = sys.argv[1]

print(f"""
USE yellow;
ALTER TABLE modules ADD COLUMN IF NOT EXISTS enabled BOOLEAN NOT NULL DEFAULT TRUE;


USE yellow_module_org_libersoft_messages;

ALTER TABLE messages ADD COLUMN IF NOT EXISTS format VARCHAR(16) NOT NULL DEFAULT "plaintext";
ALTER TABLE file_uploads
       ADD from_user_uid varchar(255) NOT NULL AFTER from_user_id,
       CHANGE created created timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP AFTER chunks_received;

""")
