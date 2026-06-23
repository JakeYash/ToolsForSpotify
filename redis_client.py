import redis
pool = redis.ConnectionPool(host='redis', port=6379)
r = redis.Redis(connection_pool=pool)
