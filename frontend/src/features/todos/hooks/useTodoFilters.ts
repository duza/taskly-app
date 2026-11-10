import { useState } from 'react'
import type { Filter, PriorityFilter, Sort, Todo } from '../types'
import { selectTodos } from '../utils/todos'

export function useTodoFilters(todos: Todo[]) {
  const [filter, setFilter] = useState<Filter>('all')
  const [search, setSearch] = useState('')
  const [sort, setSort] = useState<Sort>('newest')
  const [priority, setPriority] = useState<PriorityFilter>('all')
  return {
    filter,
    setFilter,
    search,
    setSearch,
    sort,
    setSort,
    priority,
    setPriority,
    visible: selectTodos(todos, filter, search, sort, priority),
  }
}
