import sqlite3

conn = sqlite3.connect('./db/aavatar.db')
c = conn.cursor()
# Create tables

c.execute('''DROP TABLE IF EXISTS twit_users''')
c.execute('''DROP TABLE IF EXISTS twit_friends''')
c.execute('''CREATE TABLE twit_friends
            (id INT NOT NULL UNIQUE, id_str VARCHAR(255), name VARCHAR(255), screen_name VARCHAR(255), location VARCHAR(255), description VARCHAR(255), display_url VARCHAR(255), protected BOOLEAN, followers_count INT, friends_count INT, listed_count INT, created_at VARCHAR(255), favourites_count INT, verified BOOLEAN, statuses_count INT, lang VARCHAR(255))''')


c.execute('''DROP TABLE IF EXISTS twit_followers''')
c.execute('''CREATE TABLE twit_followers
            (id INT NOT NULL UNIQUE, id_str VARCHAR(255), name VARCHAR(255), screen_name VARCHAR(255), location VARCHAR(255), description VARCHAR(255), display_url VARCHAR(255), protected BOOLEAN, followers_count INT, friends_count INT, listed_count INT, created_at VARCHAR(255), favourites_count INT, verified BOOLEAN, statuses_count INT, lang VARCHAR(255))''')



c.execute('''DROP TABLE IF EXISTS aa_users''')
c.execute(
    '''CREATE TABLE aa_users (id INT NOT NULL UNIQUE, user_added_date NOT NULL DEFAULT current_timestamp, following BOOLEAN, followed_by BOOLEAN)''')
# Save (commit) the changes
conn.commit()
conn.close()
