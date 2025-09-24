import { Route, Routes } from 'react-router-dom'

import App from '../App'
import Dashboard from '../pages/Dashboard'
import NotFound from '../pages/NotFound'

const AppRoutes = () => {
  return (
    <Routes>
      <Route path="/" element={<App />}>
        <Route index element={<Dashboard />} />
        <Route path="*" element={<NotFound />} />
      </Route>
    </Routes>
  )
}

export default AppRoutes

