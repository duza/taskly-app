import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import type { ReactNode } from 'react'
import { describe, expect, it } from 'vitest'
import { todoKeys } from '../api/queryKeys'
import { useTodosBusy } from './useTodosBusy'

function setup() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
  return { queryClient, ...renderHook(() => useTodosBusy(), { wrapper }) }
}

describe('useTodosBusy', () => {
  it('is false when no mutation is running', () => {
    const { result } = setup()
    expect(result.current).toBe(false)
  })

  it('is true while a todo mutation is pending and false after it settles', async () => {
    const { queryClient, result } = setup()
    let finish: () => void = () => {}
    const pending = new Promise<void>((resolve) => {
      finish = resolve
    })

    act(() => {
      void queryClient
        .getMutationCache()
        .build(queryClient, {
          mutationKey: todoKeys.update,
          mutationFn: () => pending,
        })
        .execute(undefined)
    })
    await waitFor(() => expect(result.current).toBe(true))

    await act(async () => {
      finish()
      await pending
    })
    await waitFor(() => expect(result.current).toBe(false))
  })

  it('ignores mutations outside the todos key', async () => {
    const { queryClient, result } = setup()
    let finish: () => void = () => {}
    const pending = new Promise<void>((resolve) => {
      finish = resolve
    })

    act(() => {
      void queryClient
        .getMutationCache()
        .build(queryClient, {
          mutationKey: ['other'],
          mutationFn: () => pending,
        })
        .execute(undefined)
    })

    expect(result.current).toBe(false)
    await act(async () => {
      finish()
      await pending
    })
  })
})
