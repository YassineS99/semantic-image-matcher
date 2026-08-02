# Frontend — Image–Post Matcher

React frontend for the semantic-image-matcher project (see the main repo
README for the full system overview, architecture, and results).

## What this does

- Type a post about an animal (e.g. "This little red fox visited my backyard").
- The app creates the post, embeds it, and runs it through the matching +
  mismatch guard pipeline via the backend API.
- Shows the best matching image, plus all candidates — correctly rejected
  candidates (e.g. a coyote suggested for a wolf post) are shown grayed out
  with the guard's explanation.
- Click any suggested (green) candidate to make it the active best match.

## Running locally

Requires the backend API running first (see the main repo README).

```bash
npm install
npm start
```

Opens at http://localhost:3000. Expects the backend API at http://localhost:8000.

## Built with

Create React App (no ejected config).