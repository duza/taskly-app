import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import { todoKeys } from '../api/queryKeys'
import { todosApi } from '../api/todos'
import type { TodoInput } from '../types'
import { useCreateTodoMutation } from './useCreateTodoMutation'

vi.mock('../api/todos', () => ({
  todosApi: { create: vi.fn() },
}))

const input: TodoInput = {
  title: 'Prepare a demo',
  description: '',
  priority: 'medium',
  due_date: null,
  completed: false,
}

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return {
    queryClient,
    ...renderHook(() => useCreateTodoMutation(), { wrapper }),
  }
}

describe('useCreateTodoMutation', () => {
  beforeEach(() => {
    vi.mocked(todosApi.create).mockReset()
  })

  it('calls the API with the input and prepends the saved todo to the cache', async () => {
    const existing = { ...todoFixture, id: 1 }
    vi.mocked(todosApi.create).mockResolvedValue(todoFixture)
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [existing])

    await act(() => result.current.mutateAsync(input))

    expect(todosApi.create).toHaveBeenCalledWith(input)
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([
      todoFixture,
      existing,
    ])
  })

  it('creates the list when the cache is empty', async () => {
    vi.mocked(todosApi.create).mockResolvedValue(todoFixture)
    const { queryClient, result } = setup()

    await act(() => result.current.mutateAsync(input))

    expect(queryClient.getQueryData(todoKeys.list)).toEqual([todoFixture])
  })

  it('deduplicates a todo already present in the cache', async () => {
    const stale = { ...todoFixture, title: 'Old title' }
    const other = { ...todoFixture, id: 2 }
    vi.mocked(todosApi.create).mockResolvedValue(todoFixture)
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [other, stale])

    await act(() => result.current.mutateAsync(input))

    expect(queryClient.getQueryData(todoKeys.list)).toEqual([
      todoFixture,
      other,
    ])
  })

  it('leaves the cache untouched when the API fails', async () => {
    vi.mocked(todosApi.create).mockRejectedValue(new Error('boom'))
    const { queryClient, result } = setup()
    queryClient.setQueryData(todoKeys.list, [])

    act(() => result.current.mutate(input))

    await waitFor(() => expect(result.current.isError).toBe(true))
    expect(queryClient.getQueryData(todoKeys.list)).toEqual([])
  })
})
