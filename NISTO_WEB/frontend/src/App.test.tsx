import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'

import AppRoutes from './routes/AppRoutes'

describe('App shell', () => {
  it('renders application title and sections', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <AppRoutes />
      </MemoryRouter>,
    )

    expect(screen.getByText('NISTO Web')).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /devices/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /connections/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: /properties/i })).toBeInTheDocument()
  })
})
