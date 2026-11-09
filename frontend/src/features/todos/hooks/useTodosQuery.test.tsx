import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import { useTodosQuery } from './useTodosQuery'

vi.mock('../api/todos', () => ({
  todosApi: { list: vi.fn() },
}))

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return { queryClient, ...renderHook(() => useTodosQuery(), { wrapper }) }
}

describe('useTodosQuery', () => {
  beforeEach(() => {
    vi.mocked(todosApi.list).mockReset()
  })

  it('loads todos, passing an abort signal, and stores them under the list key', async () => {
    vi.mocked(todosApi.list).mockResolvedValue([todoFixture])
    const { queryClient, result } = setup()

    expect(result.current.isPending).toBe(true)
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual([todoFixture])
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([todoFixture])
    expect(todosApi.list).toHaveBeenCalledWith(expect.any(AbortSignal))
  })

  it('exposes the error when loading fails', async () => {
    const error = new Error('boom')
    vi.mocked(todosApi.list).mockRejectedValue(error)
    const { result } = setup()

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBe(error)
  })
})
