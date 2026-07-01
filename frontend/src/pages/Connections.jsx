import React from 'react';

export default function Connections() {
  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">Enterprise Data Connection Manager</h1>
      <div className="bg-white p-4 rounded shadow">
        <p>Manage your data sources here. (PostgreSQL, MySQL, Snowflake, etc.)</p>
        <button className="mt-4 px-4 py-2 bg-blue-600 text-white rounded">Add Connection</button>
      </div>
    </div>
  );
}
