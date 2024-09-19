local redis_key = KEYS[1]
local quantity = tonumber(ARGV[1])
local period = tonumber(ARGV[2])

if period <= 0 then
    period = 1
elseif quantity <= 0 then
    quantity = 1
end

local QIANFAN_PREFIX = "qianfan_"
local TIME_STAMP_PREFIX = QIANFAN_PREFIX .. "last_timestamp_"
local QUANTITY_PREFIX = QIANFAN_PREFIX .. "quantity_"
local PERIOD_PREFIX = QIANFAN_PREFIX .. "period_"

local quantity_key = QUANTITY_PREFIX .. redis_key
local period_key = PERIOD_PREFIX .. redis_key

local current_quantity = tonumber(redis.call("GET", quantity_key)) or 1
local current_period = tonumber(redis.call("GET", period_key)) or 0

if current_period == 0 or quantity / period < current_quantity / current_period then
    local current_timestamp = tonumber(redis.call("TIME")[1])
    local time_key = TIME_STAMP_PREFIX .. redis_key

    redis.call("SET", time_key, current_timestamp)
    redis.call("SET", quantity_key, quantity)
    redis.call("SET", period_key, period)
end