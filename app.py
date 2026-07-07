import os
import random
from flask import Flask, jsonify, request
import psycopg2
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# 1. 从环境变量中读取 Neon 数据库连接字符串
# 本地测试时，如果环境变量为空，会尝试读取写死的字符串（记得换成你自己的 Neon 地址）
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://neondb_owner:npg_UuP2F0YpxivD@ep-bitter-bird-ao4ytzpt.c-2.ap-southeast-1.aws.neon.tech/neondb?sslmode=require'
)


def get_db_connection():
    """获取数据库连接的辅助函数"""
    # cursor_factory=RealDictCursor 可以让查询结果以字典键值对形式返回，方便转成 JSON
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


def init_db():
    """初始化数据库：如果表不存在则创建"""
    conn = get_db_connection()
    cur = conn.cursor()
    # 创建一个名为 wheel_options 的表
    cur.execute('''
                CREATE TABLE IF NOT EXISTS wheel_options
                (
                    id
                    SERIAL
                    PRIMARY
                    KEY,
                    name
                    VARCHAR
                (
                    50
                ) NOT NULL UNIQUE
                    );
                ''')
    # 插入一些初始默认选项（如果表是空的）
    cur.execute("SELECT COUNT(*) FROM wheel_options;")
    if cur.fetchone()['count'] == 0:
        default_options = ['火锅']
        for option in default_options:
            cur.execute("INSERT INTO wheel_options (name) VALUES (%s);", (option,))

    conn.commit()
    cur.close()
    conn.close()


# 执行数据库初始化
init_db()


@app.route('/api/get_options', methods=['GET'])
def get_options():
    """接口 1：获取所有转盘选项"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM wheel_options ORDER BY id ASC;")
        rows = cur.fetchall()
        options = [row['name'] for row in rows]
        cur.close()
        conn.close()
        return jsonify({"options": options})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/add_option', methods=['POST'])
def add_option():
    """接口 2：添加新选项"""
    data = request.json
    new_option = data.get('option', '').strip()

    if not new_option:
        return jsonify({"error": "选项不能为空"}), 400

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        # 使用 ON CONFLICT DO NOTHING 防止重复插入报错
        cur.execute(
            "INSERT INTO wheel_options (name) VALUES (%s) ON CONFLICT (name) DO NOTHING;",
            (new_option,)
        )
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/delete_option', methods=['POST'])
def delete_option():
    """接口 3：删除指定选项"""
    data = request.json
    option_to_delete = data.get('option', '').strip()

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM wheel_options WHERE name = %s;", (option_to_delete,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/spin', methods=['POST'])
def spin():
    """接口 4：核心抽奖逻辑（从数据库实时捞取选项进行随机）"""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT name FROM wheel_options;")
        rows = cur.fetchall()
        cur.close()
        conn.close()

        current_options = [row['name'] for row in rows]
        if not current_options:
            return jsonify({"error": "数据库中没有选项"}), 400

        # 后端计算中奖结果
        winner_index = random.randint(0, len(current_options) - 1)
        return jsonify({
            "winner_index": winner_index,
            "winner_name": current_options[winner_index]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)


# 这是一个用来测试 Git 命令行推送的超级注释！