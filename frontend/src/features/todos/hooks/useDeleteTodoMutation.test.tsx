import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import { useDeleteTodoMutation } from './useDeleteTodoMutation'

vi.mock('../api/todos', () => ({
  todosApi: { remove: vi.fn() },
}))

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return {
    queryClient,
    ...renderHook(() => useDeleteTodoMutation(), { wrapper }),
  }
}

describe('useDeleteTodoMutation', () => {
  beforeEach(() => {
    vi.mocked(todosApi.remove).mockReset()
  })

  it('removes the deleted todo from the cached list', async () => {
    const other = { ...todoFixture, id: 8 }
    vi.mocked(todosApi.remove).mockResolvedValue(undefined)
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [todoFixture, other])

    await act(() => result.current.mutateAsync(todoFixture.id))

    expect(todosApi.remove).toHaveBeenCalledWith(todoFixture.id)
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([other])
  })

  it('does not create a list when none is cached', async () => {
    vi.mocked(todosApi.remove).mockResolvedValue(undefined)
    const { queryClient, result } = setup()

    await act(() => result.current.mutateAsync(todoFixture.id))

    expect(queryClient.getQueryData(todoKeys.list)).toBeUndefined()
  })

  it('keeps the cache when the API fails', async () => {
    vi.mocked(todosApi.remove).mockRejectedValue(new Error('boom'))
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [todoFixture])

    act(() => result.current.mutate(todoFixture.id))

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([todoFixture])
  })
})
