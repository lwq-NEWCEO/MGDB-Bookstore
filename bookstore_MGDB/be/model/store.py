from pymongo import MongoClient


class Store:
    def __init__(self, db_url):
        self.client = MongoClient(db_url)
        self.db = self.client['bookstore']
        self.init_collections()

    def init_collections(self):
        self.user_col = self.db['user']
        self.store_col = self.db['store']
        self.book_col = self.db['books']
        self.order_detail_col = self.db['order_detail']
        self.order_col = self.db['order']

        # --- 现有索引 ---
        # 商店ID的唯一索引
        self.store_col.create_index([("store_id", 1)], unique=True)
        # 用户ID的唯一索引
        self.user_col.create_index([("user_id", 1)], unique=True)
        # 书籍的全文索引，用于模糊搜索和内容匹配
        self.book_col.create_index(
            [("title", "text"), ("tags", "text"), ("book_intro", "text"), ("content", "text")]
        )

        # --- 新增的优化索引 ---

        # 1. book 文档集上的更多精确匹配索引
        # 书籍ID的唯一索引，用于快速查找特定书籍
        self.book_col.create_index([("id", 1)], unique=True)
        # 标题的普通升序索引，用于精确匹配或前缀匹配的标题搜索
        self.book_col.create_index([("title", 1)])
        # 作者的普通升序索引，用于按作者进行快速搜索
        self.book_col.create_index([("author", 1)])
        # 标签的多键升序索引，用于精确匹配标签的查询
        self.book_col.create_index([("tags", 1)])

        # 2. order 文档集上的索引，用于优化订单查询和状态管理
        # 订单ID的唯一索引，用于所有订单操作的核心查找
        self.order_col.create_index([("order_id", 1)], unique=True)
        # 复合索引：用户ID（用于筛选买家历史订单）和创建时间（用于按最新订单排序）
        self.order_col.create_index([("user_id", 1), ("create_time", -1)])
        # 复合索引：订单状态（用于筛选特定状态订单）和创建时间（用于超时取消等后台任务）
        self.order_col.create_index([("status", 1), ("create_time", 1)])

        # 3. order_detail 文档集上的索引，用于快速获取订单详情
        # 订单ID的普通升序索引，用于通过 order_id 查找关联的订单详情
        self.order_detail_col.create_index([("order_id", 1)])

        # 4. (可选进阶) store 文档集嵌入式书籍ID索引
        # 如果经常需要查询某个商店内是否存在特定书籍，可以在此处添加。
        # self.store_col.create_index([("books.book_id", 1)])


database_instance = None


def init_database(db_url):
    global database_instance
    database_instance = Store(db_url)


def get_db_conn():
    global database_instance
    # 确保只初始化一次数据库连接，或者每次都重新连接（根据项目需求，这里保持原样）
    # 如果 database_instance 已经存在，可能不需要重新创建。
    # 但根据您原代码的get_db_conn逻辑，每次都会重新连接，这在某些场景下可能不是最优。
    # 如果要实现单例模式，可以修改如下：
    # if database_instance is None:
    db_url = "mongodb://localhost:27017/"
    database_instance = Store(db_url)
    return database_instance

