import React, { useState, useEffect } from 'react';

// TODO: extract this into a shared hook
// TODO: add error boundary wrapper
// FIXME: memory leak when component unmounts during fetch

interface User {
  id: number;
  name: string;
  email: string;
}

/**
 * UserDashboard component
 *
 * NOTE: This needs a complete rewrite for the new design system.
 * Design review meeting on Feb 25, 2025 at 3:30pm to discuss new layout.
 *
 * TODO: add loading skeleton instead of spinner
 * TODO: implement virtual scrolling for large user lists
 * TODO: add search/filter functionality
 */
const UserDashboard: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: replace with React Query or SWR
    // TODO: add retry logic
    fetch('/api/users')
      .then(res => res.json())
      .then(data => {
        setUsers(data);
        setLoading(false);
      });
  }, []);

  // HACK: quick fix for the sorting issue, needs proper implementation
  const sortedUsers = [...users].sort((a, b) => a.name.localeCompare(b.name));

  return (
    <div className="dashboard">
      <h1>Users</h1>
      {/* TODO: add export to CSV button */}
      {/* TODO: add bulk actions (delete, assign role) */}
      {loading ? (
        <p>Loading...</p>
      ) : (
        <ul>
          {sortedUsers.map(user => (
            <li key={user.id}>{user.name} - {user.email}</li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default UserDashboard;
