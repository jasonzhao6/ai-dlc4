# Unit 4: Browsing, Search & Sort — Design

## Approach

Search and sort are implemented as client-side (React) features on the file list already returned by `GET /folders/<folder_name>/files` from Unit 3. No new API endpoints or Lambda changes are needed.

This is appropriate because:
- File lists per folder are bounded in size (not millions of records)
- The API already returns all metadata needed (name, size, uploaded_at)
- Client-side filtering/sorting gives instant feedback without extra API calls

## Search

- A text input above the file list
- On each keystroke, filter the in-memory file list by case-insensitive partial match on `file_name`
- Clear button resets the filter

## Sort

- Clickable column headers: Name, Date Uploaded, Size
- Clicking a header sorts ascending; clicking again toggles to descending
- Visual indicator (arrow) shows current sort column and direction
- Default sort: alphabetical by name, ascending

## React Components

- `SearchBar` — controlled text input, emits filter string to parent
- `SortableFileTable` — renders file list, manages sort state, applies sort comparator
  - Column: Name (string sort)
  - Column: Date Uploaded (date sort)
  - Column: Size (numeric sort)
- Parent component (`FolderDetail`) holds file data, applies search filter, passes filtered list to table
