local redis_key = KEYS[1]
local ttl = 3600  -- 过期时间为 3600 秒

local QIANFAN_PREFIX = "qianfan_"
local TIME_STAMP_PREFIX = QIANFAN_PREFIX .. "last_timestamp_"
local KEY_PREFIX = QIANFAN_PREFIX .. "keys_"
local QUANTITY_PREFIX = QIANFAN_PREFIX .. "quantity_"
local PERIOD_PREFIX = QIANFAN_PREFIX .. "period_"

local time_key = TIME_STAMP_PREFIX .. redis_key
local cap_key = KEY_PREFIX .. redis_key
local quantity_key = QUANTITY_PREFIX .. redis_key
local period_key = PERIOD_PREFIX .. redis_key

local keys = {time_key, cap_key, quantity_key, period_key}

for i, key in pairs(keys) do
    if redis.call("EXISTS", key) == 1 then
        -- 键存在，设置新的过期时间
        redis.call("EXPIRE", key, ttl)
    end
end

return true