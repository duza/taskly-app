import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { request } from './http'

const fetchMock = vi.fn()

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status })
}

describe('request', () => {
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('prefixes the path with /api and sends a JSON content type', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }))

    await request('/todos')

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [url, init] = fetchMock.mock.calls[0]
    expect(url).toBe('/api/todos')
    expect(init.headers).toEqual({ 'Content-Type': 'application/json' })
  })

  it('forwards init options and lets callers override headers', async () => {
    fetchMock.mockResolvedValue(jsonResponse({}))

    await request('/todos', {
      method: 'POST',
      body: '{"title":"a"}',
      headers: { 'Content-Type': 'text/plain', 'X-Test': '1' },
    })

    const [, init] = fetchMock.mock.calls[0]
    expect(init.method).toBe('POST')
    expect(init.body).toBe('{"title":"a"}')
    expect(init.headers).toEqual({
      'Content-Type': 'text/plain',
      'X-Test': '1',
    })
  })

  it('returns the parsed JSON body on success', async () => {
    fetchMock.mockResolvedValue(jsonResponse([{ id: 1 }]))

    await expect(request('/todos')).resolves.toEqual([{ id: 1 }])
  })

  it('returns undefined for a 204 response', async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await expect(
      request('/todos/1', { method: 'DELETE' }),
    ).resolves.toBeUndefined()
  })

  it('throws a validation message for a 422 response', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'ignored' }, 422))

    await expect(request('/todos')).rejects.toThrow(
      'Check the task details: title up to 120 characters, description up to 2000 characters, and a valid due date.',
    )
  })

  it('throws the detail string for other error responses', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: 'Todo not found' }, 404))

    await expect(request('/todos/9')).rejects.toThrow('Todo not found')
  })

  it('throws a generic message when detail is not a string', async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: [{ msg: 'x' }] }, 400))

    await expect(request('/todos')).rejects.toThrow(
      'The operation failed. Please try again.',
    )
  })

  it('throws a generic message when the error body is not JSON', async () => {
    fetchMock.mockResolvedValue(
      new Response('<html>boom</html>', { status: 500 }),
    )

    await expect(request('/todos')).rejects.toThrow(
      'The operation failed. Please try again.',
    )
  })

  it('throws a connection message when fetch fails', async () => {
    fetchMock.mockRejectedValue(new TypeError('Failed to fetch'))

    await expect(request('/todos')).rejects.toThrow(
      'Cannot connect to the server. Please try again.',
    )
  })

  it('rethrows the original error when the request was aborted', async () => {
    const controller = new AbortController()
    controller.abort()
    const abortError = new DOMException('Aborted', 'AbortError')
    fetchMock.mockRejectedValue(abortError)

    await expect(request('/todos', { signal: controller.signal })).rejects.toBe(
      abortError,
    )
  })
})
