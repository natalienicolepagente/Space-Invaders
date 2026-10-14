import hashlib
import hmac
import os

import mysql.connector
from mysql.connector import Error

DB_NAME = "pagente_space_invaders_db"

HASH_PREFIX = "pbkdf2"
HASH_ITERATIONS = 100_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, HASH_ITERATIONS
    )
    return f"{HASH_PREFIX}${HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password, stored):
    try:
        prefix, iterations, salt_hex, hash_hex = stored.split("$")

        if prefix != HASH_PREFIX:
            return False

        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"),
            bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)

    except (ValueError, AttributeError):
        return False


def create_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            database=DB_NAME,
            user="root",
            password=""
        )

        if connection.is_connected():
            return connection

    except Error as e:
        print(f"Database Connection Error: {e}")

    return None


def get_db_connection():
    return create_connection()


def setup_database():
    conn = create_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS players (
                player_id INT AUTO_INCREMENT PRIMARY KEY,
                username VARCHAR(50) NOT NULL UNIQUE,
                password VARCHAR(255) NOT NULL,
                ship INT NOT NULL DEFAULT 1,
                avatar INT NOT NULL DEFAULT 1,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scores (
                score_id INT AUTO_INCREMENT PRIMARY KEY,
                player_id INT NOT NULL,
                score INT NOT NULL DEFAULT 0,
                wave INT NOT NULL DEFAULT 1,
                date_added TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (player_id)
                    REFERENCES players(player_id)
                    ON DELETE CASCADE
            )
        """)

        cursor.execute("SHOW COLUMNS FROM players")
        player_columns = [row[0] for row in cursor.fetchall()]

        if "ship" not in player_columns:
            cursor.execute(
                "ALTER TABLE players "
                "ADD COLUMN ship INT NOT NULL DEFAULT 1"
            )

        if "avatar" not in player_columns:
            cursor.execute(
                "ALTER TABLE players "
                "ADD COLUMN avatar INT NOT NULL DEFAULT 1"
            )

        cursor.execute("SHOW COLUMNS FROM scores")
        score_columns = [row[0] for row in cursor.fetchall()]

        if "wave" not in score_columns:
            cursor.execute(
                "ALTER TABLE scores "
                "ADD COLUMN wave INT NOT NULL DEFAULT 1"
            )

        if "date_added" not in score_columns:
            cursor.execute(
                "ALTER TABLE scores "
                "ADD COLUMN date_added TIMESTAMP NOT NULL "
                "DEFAULT CURRENT_TIMESTAMP"
            )

        cursor.execute(
            "SELECT player_id, password FROM players "
            "WHERE password NOT LIKE %s",
            (HASH_PREFIX + "$%",)
        )

        for player_id, plain in cursor.fetchall():
            cursor.execute(
                "UPDATE players SET password = %s WHERE player_id = %s",
                (hash_password(plain), player_id)
            )

        conn.commit()
        return True

    except Error as e:
        print(f"Database Setup Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def register_player(username, password):
    conn = get_db_connection()

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players WHERE username = %s",
            (username,)
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "INSERT INTO players (username, password) VALUES (%s, %s)",
            (username, hash_password(password))
        )

        conn.commit()
        return True, "ACCOUNT CREATED"

    except Error as e:
        conn.rollback()
        print(f"Registration Error: {e}")
        return False, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def login_player(username, password):
    conn = get_db_connection()

    if not conn:
        print("Login Error: Database connection failed")
        return None

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT player_id, username, password, ship, avatar
            FROM players
            WHERE username = %s
            """,
            (username,)
        )

        player = cursor.fetchone()

        if not player or not verify_password(password, player["password"]):
            return None

        player.pop("password", None)
        return player

    except Error as e:
        print(f"Login Error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def update_profile(player_id, username, ship, avatar):
    conn = get_db_connection()

    if not conn:
        return False, "DATABASE CONNECTION FAILED"

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT player_id FROM players "
            "WHERE username = %s AND player_id <> %s",
            (username, player_id)
        )

        if cursor.fetchone():
            return False, "USERNAME ALREADY EXISTS"

        cursor.execute(
            "UPDATE players SET username = %s, ship = %s, avatar = %s "
            "WHERE player_id = %s",
            (username, ship, avatar, player_id)
        )

        conn.commit()
        return True, "PROFILE SAVED"

    except Error as e:
        conn.rollback()
        print(f"Profile Update Error: {e}")
        return False, "DATABASE ERROR"

    finally:
        cursor.close()
        conn.close()


def save_score(player_id, score, wave=1):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            INSERT INTO scores (player_id, score, wave, date_added)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            """,
            (player_id, score, wave)
        )

        conn.commit()
        return True

    except Error as e:
        print(f"Score Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


def load_leaderboard(limit=8):
    conn = get_db_connection()

    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT p.player_id, p.username, s.score, s.wave, s.date_added
            FROM scores s
            INNER JOIN players p ON p.player_id = s.player_id
            WHERE s.score_id = (
                SELECT s2.score_id
                FROM scores s2
                WHERE s2.player_id = s.player_id
                ORDER BY s2.score DESC, s2.date_added DESC, s2.score_id DESC
                LIMIT 1
            )
            ORDER BY s.score DESC, s.date_added ASC
            LIMIT %s
            """,
            (limit,)
        )

        return cursor.fetchall()

    except Error as e:
        print(f"Leaderboard Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_player_scores(player_id, limit=8):
    conn = get_db_connection()

    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            """
            SELECT score, wave, date_added
            FROM scores
            WHERE player_id = %s
            ORDER BY date_added DESC, score_id DESC
            LIMIT %s
            """,
            (player_id, limit)
        )

        return cursor.fetchall()

    except Error as e:
        print(f"Player Scores Error: {e}")
        return []

    finally:
        cursor.close()
        conn.close()


def get_player_stats(player_id):
    stats = {
        "total_score": 0,
        "games_played": 0,
        "highest_score": 0,
        "highest_wave": 0,
    }

    conn = get_db_connection()

    if not conn:
        return stats

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COALESCE(SUM(score), 0),
                   COUNT(*),
                   COALESCE(MAX(score), 0),
                   COALESCE(MAX(wave), 0)
            FROM scores
            WHERE player_id = %s
            """,
            (player_id,)
        )

        row = cursor.fetchone()

        if row:
            stats["total_score"] = int(row[0])
            stats["games_played"] = int(row[1])
            stats["highest_score"] = int(row[2])
            stats["highest_wave"] = int(row[3])

        return stats

    except Error as e:
        print(f"Stats Error: {e}")
        return stats

    finally:
        cursor.close()
        conn.close()


def get_player_rank(player_id):
    conn = get_db_connection()

    if not conn:
        return None

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
            SELECT COUNT(*) + 1
            FROM (
                SELECT player_id, MAX(score) AS best
                FROM scores
                GROUP BY player_id
            ) t
            WHERE t.best > (
                SELECT COALESCE(MAX(score), 0)
                FROM scores
                WHERE player_id = %s
            )
            """,
            (player_id,)
        )

        row = cursor.fetchone()
        return int(row[0]) if row else None

    except Error as e:
        print(f"Rank Error: {e}")
        return None

    finally:
        cursor.close()
        conn.close()


def delete_player(player_id):
    conn = get_db_connection()

    if not conn:
        return False

    cursor = conn.cursor()

    try:
        cursor.execute(
            "DELETE FROM players WHERE player_id = %s", (player_id,)
        )
        conn.commit()
        return True

    except Error as e:
        print(f"Delete Error: {e}")
        conn.rollback()
        return False

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    if setup_database():
        print("DATABASE READY")
    else:
        print("DATABASE SETUP FAILED")