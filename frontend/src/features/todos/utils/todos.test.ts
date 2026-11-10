import { describe, expect, it } from 'vitest'
import { selectTodos } from './todos'
import type { Todo } from '../types'

const base: Todo = {
  id: 1,
  title: 'Sprint plan',
  description: '',
  priority: 'medium',
  completed: false,
  due_date: null,
  created_at: '2026-10-01T12:00:00Z',
  updated_at: '2026-10-01T12:00:00Z',
}

describe('selectTodos', () => {
  it('combines status with a case-insensitive search in the description', () => {
    const matching = { ...base, description: 'Discuss the API' }
    const todos = [
      matching,
      { ...matching, id: 2, completed: true },
      { ...base, id: 3 },
    ]
    expect(selectTodos(todos, 'active', ' api ', 'newest')).toEqual([matching])
  })

  it('filters by priority and treats "all" as no priority filter', () => {
    const high: Todo = { ...base, id: 2, priority: 'high' }
    const low: Todo = { ...base, id: 3, priority: 'low' }
    const todos = [base, high, low]
    expect(selectTodos(todos, 'all', '', 'newest', 'high')).toEqual([high])
    expect(selectTodos(todos, 'all', '', 'newest', 'all')).toHaveLength(3)
    expect(selectTodos(todos, 'all', '', 'newest')).toHaveLength(3)
  })

  it('combines priority with status and search', () => {
    const match: Todo = { ...base, id: 2, priority: 'high', title: 'Fix bug' }
    const todos: Todo[] = [
      match,
      { ...match, id: 3, completed: true },
      { ...match, id: 4, priority: 'low' },
      { ...match, id: 5, title: 'Other' },
    ]
    expect(selectTodos(todos, 'active', 'bug', 'newest', 'high')).toEqual([
      match,
    ])
  })

  it('sorts by priority without changing the source array', () => {
    const high: Todo = { ...base, id: 2, priority: 'high' }
    const todos = [base, high]
    expect(selectTodos(todos, 'all', '', 'priority')).toEqual([high, base])
    expect(todos).toEqual([base, high])
  })
})
