local redis_key = KEYS[1]

local QIANFAN_PREFIX = "qianfan_"
local TIME_STAMP_PREFIX = QIANFAN_PREFIX .. "last_timestamp_"
local KEY_PREFIX = QIANFAN_PREFIX .. "keys_"
local QUANTITY_PREFIX = QIANFAN_PREFIX .. "quantity_"
local PERIOD_PREFIX = QIANFAN_PREFIX .. "period_"

local time_key = TIME_STAMP_PREFIX .. redis_key
local cap_key = KEY_PREFIX .. redis_key
local quantity_key = QUANTITY_PREFIX .. redis_key
local period_key = PERIOD_PREFIX .. redis_key

local quantity = tonumber(redis.call("GET", quantity_key)) or 1
local period = tonumber(redis.call("GET", period_key)) or 1
local qpp = quantity / period

local current_timestamp = tonumber(redis.call("TIME")[1])
local last_timestamp = tonumber(redis.call("GET", time_key))
local time_diff = current_timestamp - last_timestamp

local current_cap = tonumber(redis.call("GET", cap_key)) or 0
local increment = qpp * time_diff

current_cap = math.min(current_cap + increment, quantity) - 1

redis.call("SET", time_key, current_timestamp)
redis.call("SET", cap_key, current_cap)

if current_cap >= 0 then
    return 0
else
    return (-current_cap) / qpp
end



