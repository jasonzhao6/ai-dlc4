import React from 'react';

function SearchBar({ searchTerm, onSearchChange }) {
  return (
    <div className="mb-3">
      <div className="input-group" style={{ maxWidth: '400px' }}>
        <span className="input-group-text"><i className="bi bi-search"></i></span>
        <input
          type="text"
          className="form-control"
          placeholder="Search files by name..."
          value={searchTerm}
          onChange={e => onSearchChange(e.target.value)}
        />
        {searchTerm && (
          <button className="btn btn-outline-secondary" onClick={() => onSearchChange('')}>
            <i className="bi bi-x-lg"></i>
          </button>
        )}
      </div>
    </div>
  );
}

export default SearchBar;
