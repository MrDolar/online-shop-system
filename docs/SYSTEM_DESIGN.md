# 系统设计文档

## 1. 架构概述

### 1.1 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│   SQLite    │
│   (React)   │     │  (FastAPI)  │     │  Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                           │
                    ┌──────┴──────┐
                    │  AI Service │
                    │ (OpenAI API)│
                    └─────────────┘
```

### 1.2 技术栈

| 组件 | 技术选型 | 说明 |
|------|---------|------|
| Web 框架 | FastAPI | 高性能异步框架，自动生成 API 文档 |
| ORM | SQLAlchemy | Python 最流行的 ORM |
| 数据库 | SQLite | 轻量级，适合开发和小型部署 |
| 认证 | JWT | 无状态认证，适合前后端分离 |
| AI | OpenAI API | 兼容多种 LLM 服务 |
| 前端 | React | 占位，后续实现 |

## 2. 目录结构

```
backend/
├── app/
│   ├── api/                # API 路由层
│   │   ├── __init__.py
│   │   ├── schemas.py      # Pydantic 数据模型
│   │   ├── auth.py         # 认证相关 API
│   │   ├── products.py     # 商品相关 API
│   │   ├── cart.py         # 购物车 API
│   │   ├── orders.py       # 订单和支付 API
│   │   ├── ai.py           # AI 功能 API
│   │   └── statistics.py   # 数据统计 API
│   ├── models/             # 数据库模型层
│   │   ├── __init__.py
│   │   ├── user.py         # 用户模型
│   │   ├── product.py      # 商品、分类、评论模型
│   │   ├── cart.py         # 购物车模型
│   │   └── order.py        # 订单、支付模型
│   ├── services/           # 业务逻辑层（预留）
│   │   └── __init__.py
│   ├── core/               # 核心配置
│   │   ├── __init__.py
│   │   ├── config.py       # 应用配置
│   │   ├── database.py     # 数据库连接
│   │   └── security.py     # 安全相关（JWT、密码）
│   ├── __init__.py
│   └── main.py             # 应用入口
├── requirements.txt
├── Dockerfile
└── .env.example
```

## 3. 数据库设计

### 3.1 ER 图

```
User ──┬── CartItem ──── Product
       │                    │
       ├── Order ────────── OrderItem
       │    │
       │    └── Payment
       │
       └── Review ──────── Product
                               │
                           Category
```

### 3.2 表结构

#### users 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| username | VARCHAR(50) UNIQUE | 用户名 |
| email | VARCHAR(100) UNIQUE | 邮箱 |
| hashed_password | VARCHAR(128) | 密码哈希 |
| full_name | VARCHAR(100) | 姓名 |
| phone | VARCHAR(20) | 电话 |
| address | VARCHAR(500) | 地址 |
| is_active | BOOLEAN | 是否激活 |
| is_admin | BOOLEAN | 是否管理员 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### categories 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | VARCHAR(100) UNIQUE | 分类名 |
| description | VARCHAR(500) | 描述 |
| parent_id | INTEGER FK | 父分类ID |
| created_at | DATETIME | 创建时间 |

#### products 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| name | VARCHAR(200) | 商品名 |
| description | TEXT | 描述 |
| price | FLOAT | 价格 |
| original_price | FLOAT | 原价 |
| stock | INTEGER | 库存 |
| category_id | INTEGER FK | 分类ID |
| image_url | VARCHAR(500) | 图片URL |
| is_active | BOOLEAN | 是否上架 |
| sales_count | INTEGER | 销量 |
| rating | FLOAT | 评分 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### cart_items 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK | 用户ID |
| product_id | INTEGER FK | 商品ID |
| quantity | INTEGER | 数量 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### orders 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| order_number | VARCHAR(50) UNIQUE | 订单号 |
| user_id | INTEGER FK | 用户ID |
| total_amount | FLOAT | 总金额 |
| status | VARCHAR(20) | 状态 |
| shipping_address | VARCHAR(500) | 收货地址 |
| phone | VARCHAR(20) | 联系电话 |
| remark | TEXT | 备注 |
| paid_at | DATETIME | 支付时间 |
| shipped_at | DATETIME | 发货时间 |
| delivered_at | DATETIME | 送达时间 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### order_items 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| order_id | INTEGER FK | 订单ID |
| product_id | INTEGER FK | 商品ID |
| product_name | VARCHAR(200) | 商品名快照 |
| product_price | FLOAT | 价格快照 |
| quantity | INTEGER | 数量 |
| subtotal | FLOAT | 小计 |

#### payments 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| order_id | INTEGER FK UNIQUE | 订单ID |
| amount | FLOAT | 金额 |
| method | VARCHAR(50) | 支付方式 |
| status | VARCHAR(20) | 状态 |
| transaction_id | VARCHAR(100) | 交易流水号 |
| paid_at | DATETIME | 支付时间 |
| created_at | DATETIME | 创建时间 |

#### reviews 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 主键 |
| user_id | INTEGER FK | 用户ID |
| product_id | INTEGER FK | 商品ID |
| rating | INTEGER | 评分(1-5) |
| comment | TEXT | 评论内容 |
| sentiment | VARCHAR(20) | 情感倾向 |
| sentiment_score | FLOAT | 情感分数 |
| created_at | DATETIME | 创建时间 |

## 4. API 设计

### 4.1 认证机制

使用 JWT Bearer Token：
```
Authorization: Bearer <token>
```

### 4.2 API 路由总览

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | /api/auth/register | 用户注册 | 否 |
| POST | /api/auth/login | 用户登录 | 否 |
| GET | /api/auth/me | 获取当前用户 | 是 |
| PUT | /api/auth/me | 更新个人信息 | 是 |
| GET | /api/categories | 获取分类列表 | 否 |
| POST | /api/categories | 创建分类 | 管理员 |
| DELETE | /api/categories/{id} | 删除分类 | 管理员 |
| GET | /api/products | 商品列表 | 否 |
| GET | /api/products/{id} | 商品详情 | 否 |
| POST | /api/products | 创建商品 | 管理员 |
| PUT | /api/products/{id} | 更新商品 | 管理员 |
| DELETE | /api/products/{id} | 删除商品 | 管理员 |
| GET | /api/products/{id}/reviews | 商品评论 | 否 |
| POST | /api/reviews | 发表评论 | 是 |
| GET | /api/cart | 获取购物车 | 是 |
| POST | /api/cart/items | 添加到购物车 | 是 |
| PUT | /api/cart/items/{id} | 更新数量 | 是 |
| DELETE | /api/cart/items/{id} | 删除商品 | 是 |
| DELETE | /api/cart | 清空购物车 | 是 |
| POST | /api/orders | 创建订单 | 是 |
| GET | /api/orders | 订单列表 | 是 |
| GET | /api/orders/{id} | 订单详情 | 是 |
| PUT | /api/orders/{id}/cancel | 取消订单 | 是 |
| POST | /api/payments/{order_id} | 发起支付 | 是 |
| GET | /api/payments/{order_id} | 支付信息 | 是 |
| POST | /api/ai/recommend | 智能推荐 | 是 |
| POST | /api/ai/analyze-sentiment | 情感分析 | 是 |
| POST | /api/ai/chat | 智能客服 | 是 |
| GET | /api/statistics/overview | 数据概览 | 管理员 |
| GET | /api/statistics/sales-trend | 销售趋势 | 管理员 |
| GET | /api/statistics/category-stats | 分类统计 | 管理员 |

## 5. 安全设计

### 5.1 认证与授权
- JWT Token 无状态认证
- Token 有效期 24 小时
- 基于角色的权限控制（普通用户/管理员）

### 5.2 数据安全
- 密码使用 bcrypt 加密存储
- 敏感配置通过环境变量管理
- API Key 不硬编码在代码中

### 5.3 输入验证
- Pydantic 模型自动验证请求数据
- SQL 注入防护（SQLAlchemy ORM）
- 参数化查询

## 6. AI 集成设计

### 6.1 架构

```
API Request → AI Router → OpenAI Client → LLM Service
                                    ↓
                              Response Parsing
                                    ↓
                              Return Result
```

### 6.2 智能推荐算法
1. 获取用户购买历史
2. 构建商品列表上下文
3. 调用 LLM 分析用户偏好
4. 返回推荐商品及理由
5. 异常时降级为热门商品推荐

### 6.3 情感分析流程
1. 接收评论文本
2. 构建分析 prompt
3. 调用 LLM 分析
4. 解析返回的情感、分数、说明
5. 用于评论展示和商品评分

### 6.4 智能客服设计
- 维护对话上下文（内存存储）
- 系统 prompt 定义客服角色
- 保留最近 20 条对话历史
- 超出上下文时自动截断

## 7. 部署架构

### 7.1 Docker 部署

```yaml
services:
  backend:
    build: ./backend
    ports: 8000:8000
    volumes: shop_data:/app/data

  frontend:
    build: ./frontend
    ports: 3000:3000
    depends_on: backend
```

### 7.2 扩展方案
- 数据库迁移至 PostgreSQL
- 引入 Redis 缓存
- Nginx 反向代理
- Celery 异步任务
- 文件存储（OSS/S3）
