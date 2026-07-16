const DEFAULT_TIME_ZONE = 'Asia/Shanghai'

function dateValue(value: string | number | Date): Date {
  if (value instanceof Date) return value
  return new Date(typeof value === 'number' && value < 1e12 ? value * 1000 : value)
}

export function formatDateTime(value: string | number | Date, timeZone = DEFAULT_TIME_ZONE): string {
  const date = dateValue(value)
  if (Number.isNaN(date.getTime())) return '未知时间'
  return new Intl.DateTimeFormat('zh-CN', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false }).format(date).replaceAll('/', '-')
}

export function formatTimelineTime(value: string | number | Date, timeZone = DEFAULT_TIME_ZONE): string {
  const date = dateValue(value)
  if (Number.isNaN(date.getTime())) return '未知时间'
  const now = new Date()
  const parts = (item: Date) => new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(item)
  const today = parts(now)
  const yesterday = parts(new Date(now.getTime() - 86400000))
  const target = parts(date)
  const time = new Intl.DateTimeFormat('zh-CN', { timeZone, hour: '2-digit', minute: '2-digit', hour12: false }).format(date)
  if (target === today) return `今天 ${time}`
  if (target === yesterday) return `昨天 ${time}`
  return `${new Intl.DateTimeFormat('zh-CN', { timeZone, month: 'numeric', day: 'numeric' }).format(date)} ${time}`
}

export function formatTimelineDate(value: string | number | Date, timeZone = DEFAULT_TIME_ZONE): string {
  const date = dateValue(value)
  if (Number.isNaN(date.getTime())) return '未知日期'
  const now = new Date()
  const parts = (item: Date) => new Intl.DateTimeFormat('en-CA', { timeZone, year: 'numeric', month: '2-digit', day: '2-digit' }).format(item)
  const target = parts(date)
  if (target === parts(now)) return '今天'
  if (target === parts(new Date(now.getTime() - 86400000))) return '昨天'
  return new Intl.DateTimeFormat('zh-CN', { timeZone, month: 'long', day: 'numeric' }).format(date)
}

export function formatTimelineClock(value: string | number | Date, timeZone = DEFAULT_TIME_ZONE): string {
  const date = dateValue(value)
  if (Number.isNaN(date.getTime())) return '--:--'
  return new Intl.DateTimeFormat('zh-CN', {
    timeZone,
    hour: '2-digit',
    minute: '2-digit',
    hour12: false,
  }).format(date)
}
