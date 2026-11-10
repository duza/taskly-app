import { act, renderHook } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { todoFixture } from '../../../test/todoFixture'
import type { Todo } from '../types'
import { useTodoFilters } from './useTodoFilters'

const todos: Todo[] = [
  {
    ...todoFixture,
    id: 1,
    title: 'Write report',
    priority: 'low',
    created_at: '2026-10-01T10:00:00Z',
  },
  {
    ...todoFixture,
    id: 2,
    title: 'Buy milk',
    priority: 'high',
    completed: true,
    created_at: '2026-10-02T10:00:00Z',
  },
  {
    ...todoFixture,
    id: 3,
    title: 'Plan trip',
    priority: 'medium',
    created_at: '2026-10-03T10:00:00Z',
  },
]

const ids = (list: Todo[]) => list.map((todo) => todo.id)

describe('useTodoFilters', () => {
  it('starts with all todos, newest first', () => {
    const { result } = renderHook(() => useTodoFilters(todos))

    expect(result.current.filter).toBe('all')
    expect(result.current.search).toBe('')
    expect(result.current.sort).toBe('newest')
    expect(ids(result.current.visible)).toEqual([3, 2, 1])
  })

  it('filters by status', () => {
    const { result } = renderHook(() => useTodoFilters(todos))

    act(() => result.current.setFilter('completed'))
    expect(ids(result.current.visible)).toEqual([2])

    act(() => result.current.setFilter('active'))
    expect(ids(result.current.visible)).toEqual([3, 1])
  })

  it('filters by search text', () => {
    const { result } = renderHook(() => useTodoFilters(todos))

    act(() => result.current.setSearch('MILK'))

    expect(result.current.search).toBe('MILK')
    expect(ids(result.current.visible)).toEqual([2])
  })

  it('sorts by priority', () => {
    const { result } = renderHook(() => useTodoFilters(todos))

    act(() => result.current.setSort('priority'))

    expect(result.current.sort).toBe('priority')
    expect(ids(result.current.visible)).toEqual([2, 3, 1])
  })

  it('recomputes visible todos when the input list changes', () => {
    const { result, rerender } = renderHook(
      ({ list }) => useTodoFilters(list),
      { initialProps: { list: todos } },
    )

    rerender({ list: todos.slice(0, 1) })

    expect(ids(result.current.visible)).toEqual([1])
  })
})
