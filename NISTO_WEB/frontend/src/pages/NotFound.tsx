import { Link } from 'react-router-dom'

const NotFound = () => {
  return (
    <div className="panel not-found">
      <header className="panel-header">
        <h2>Page Not Found</h2>
      </header>
      <div className="panel-content">
        <p>The page you are looking for does not exist.</p>
        <Link className="primary-button" to="/">
          Return to Dashboard
        </Link>
      </div>
    </div>
  )
}

export default NotFound

