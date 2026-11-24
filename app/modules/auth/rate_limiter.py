from hashlib import sha256
from typing import cast

from redis import Redis
from redis.exceptions import RedisError

LOGIN_WINDOW_SECONDS = 60
LOGIN_IP_LIMIT = 20
LOGIN_EMAIL_LIMIT = 10

LOGIN_LIMIT_SCRIPT = """
local window_seconds = tonumber(ARGV[1])

for i, key in ipairs(KEYS) do
    local limit = tonumber(ARGV[i + 1])
    local count = redis.call("GET", key)

    if not count then
        redis.call("SET", key, 1, "EX", window_seconds)
    elseif tonumber(count) >= limit then
        return math.max(1, redis.call("TTL", key))
    else
        redis.call("INCR", key)
    end
end

return 0
"""


class RateLimiterUnavailableError(Exception):
    pass


def record_login_attempt(client: Redis, client_host: str, email: str) -> int:
    ip_digest = sha256(client_host.encode()).hexdigest()
    email_digest = sha256(email.casefold().encode()).hexdigest()
    try:
        retry_after = client.eval(
            LOGIN_LIMIT_SCRIPT,
            2,
            f"fast-server:login:ip:{ip_digest}",
            f"fast-server:login:email:{email_digest}",
            LOGIN_WINDOW_SECONDS,
            LOGIN_IP_LIMIT,
            LOGIN_EMAIL_LIMIT,
        )
    except RedisError as exc:
        raise RateLimiterUnavailableError from exc
    return cast(int, retry_after)
