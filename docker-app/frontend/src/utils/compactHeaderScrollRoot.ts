export interface CompactHeaderScrollController {
  bind: () => void
  refresh: () => void
  dispose: () => void
  getScrollRoot: () => HTMLElement | null
}

function isScrollable(element: HTMLElement) {
  const style = window.getComputedStyle(element)
  return /(auto|scroll|overlay)/.test(style.overflowY)
    && element.scrollHeight > element.clientHeight + 2
}

export function resolveCompactHeaderScrollRoot(target: HTMLElement | null) {
  let current = target?.parentElement ?? null
  while (current && current !== document.body && current !== document.documentElement) {
    if (isScrollable(current)) return current
    current = current.parentElement
  }
  return null
}

export function createCompactHeaderScrollController(
  getTarget: () => HTMLElement | null,
  onUpdate: () => void,
): CompactHeaderScrollController {
  let scrollRoot: HTMLElement | null = null
  let frame = 0
  let bound = false
  let resizeObserver: ResizeObserver | null = null

  const scheduleUpdate = () => {
    if (frame || typeof window === 'undefined') return
    frame = window.requestAnimationFrame(() => {
      frame = 0
      refreshRoot()
      onUpdate()
    })
  }

  const observeElements = () => {
    resizeObserver?.disconnect()
    if (typeof ResizeObserver === 'undefined') return
    resizeObserver = new ResizeObserver(scheduleUpdate)
    const target = getTarget()
    if (target) resizeObserver.observe(target)
    if (scrollRoot) resizeObserver.observe(scrollRoot)
  }

  const refreshRoot = () => {
    const nextRoot = resolveCompactHeaderScrollRoot(getTarget())
    if (nextRoot === scrollRoot) return
    scrollRoot?.removeEventListener('scroll', scheduleUpdate)
    if (!scrollRoot) window.removeEventListener('scroll', scheduleUpdate)
    scrollRoot = nextRoot
    if (scrollRoot) {
      scrollRoot.addEventListener('scroll', scheduleUpdate, { passive: true })
    } else {
      window.addEventListener('scroll', scheduleUpdate, { passive: true })
    }
    observeElements()
  }

  const bind = () => {
    if (bound || typeof window === 'undefined') return
    bound = true
    window.addEventListener('resize', scheduleUpdate, { passive: true })
    // Async content can make a host scrollable after mount. Capturing scroll
    // events lets the controller resolve that root on the next frame.
    window.addEventListener('scroll', scheduleUpdate, { capture: true, passive: true })
    refreshRoot()
    observeElements()
    scheduleUpdate()
  }

  const refresh = () => {
    refreshRoot()
    scheduleUpdate()
  }

  const dispose = () => {
    bound = false
    if (frame && typeof window !== 'undefined') window.cancelAnimationFrame(frame)
    frame = 0
    scrollRoot?.removeEventListener('scroll', scheduleUpdate)
    if (!scrollRoot) window.removeEventListener('scroll', scheduleUpdate)
    window.removeEventListener('scroll', scheduleUpdate, true)
    scrollRoot = null
    window.removeEventListener('resize', scheduleUpdate)
    resizeObserver?.disconnect()
    resizeObserver = null
  }

  return {
    bind,
    refresh,
    dispose,
    getScrollRoot: () => scrollRoot,
  }
}
