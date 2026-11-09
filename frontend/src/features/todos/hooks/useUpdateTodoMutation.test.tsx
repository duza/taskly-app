import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import { useUpdateTodoMutation } from './useUpdateTodoMutation'

vi.mock('../api/todos', () => ({
  todosApi: { update: vi.fn() },
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
    ...renderHook(() => useUpdateTodoMutation(), { wrapper }),
  }
}

describe('useUpdateTodoMutation', () => {
  beforeEach(() => {
    vi.mocked(todosApi.update).mockReset()
  })

  it('replaces only the updated todo in the cached list', async () => {
    const other = { ...todoFixture, id: 8 }
    const saved = { ...todoFixture, completed: true }
    vi.mocked(todosApi.update).mockResolvedValue(saved)
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [todoFixture, other])

    await act(() =>
      result.current.mutateAsync({
        id: todoFixture.id,
        input: { completed: true },
      }),
    )

    expect(todosApi.update).toHaveBeenCalledWith(todoFixture.id, {
      completed: true,
    })
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([saved, other])
  })

  it('does not create a list when none is cached', async () => {
    vi.mocked(todosApi.update).mockResolvedValue(todoFixture)
    const { queryClient, result } = setup()

    await act(() =>
      result.current.mutateAsync({ id: todoFixture.id, input: {} }),
    )

    expect(queryClient.getQueryData(todoKeys.list)).toBeUndefined()
  })

  it('keeps the cache when the API fails', async () => {
    vi.mocked(todosApi.update).mockRejectedValue(new Error('boom'))
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [todoFixture])

    act(() =>
      result.current.mutate({ id: todoFixture.id, input: { title: 'x' } }),
    )

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([todoFixture])
  })
})
