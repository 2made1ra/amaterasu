# State Management and Routing

This document explains the core mechanics of how the application tracks data (state) and how users navigate between different views (routing).

## State Management in Svelte

Unlike frameworks like React (which requires `useState` or Redux) or Vue (which uses Vuex/Pinia), Svelte has reactivity built directly into the language via the compiler.

### 1. Local Component State
In a `.svelte` file, any variable declared with `let` inside the `<script>` block is automatically reactive. When you reassign that variable, Svelte automatically updates the UI wherever that variable is used.

```html
<script>
  // This is reactive state
  let inputQuery = "";
  let isSending = false;
</script>

<!-- The UI updates automatically when inputQuery or isSending changes -->
<textarea bind:value={inputQuery}></textarea>
<button disabled={isSending}>Send</button>
```

### 2. Parent-Child Communication (Props)
Data is passed downwards from a parent component to a child component using **props**. In the child component, you declare a variable with the `export` keyword to accept a prop.

**Parent (`Dashboard.svelte`):**
```html
<!-- Passing activeDocumentId down to the Chat component -->
<Chat {activeDocumentId} />
```

**Child (`Chat.svelte`):**
```html
<script>
  // Receiving the prop
  export let activeDocumentId = null;
</script>
```

### 3. Child-Parent Communication (Events)
When a child component needs to tell a parent component that something happened (like a document was clicked), it dispatches a custom event using `createEventDispatcher`.

**Child (`DocumentUpload.svelte`):**
```html
<script>
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher();

  function selectDocument(id) {
    // Dispatch a 'documentSelected' event, passing the document ID as details
    dispatch("documentSelected", id);
  }
</script>

<div on:click={() => selectDocument(doc.id)}>...</div>
```

**Parent (`Dashboard.svelte`):**
```html
<!-- The parent listens for 'on:documentSelected' -->
<DocumentUpload on:documentSelected={(e) => activeDocumentId = e.detail} />
```

## Routing

Because this is a Single Page Application (SPA), navigating between pages (like going from Login to the Dashboard) does not require a full page reload from the server. Instead, JavaScript handles changing the view.

This project uses the `svelte-routing` library.

### 1. Defining Routes
Routes are defined in the root component, `src/App.svelte`. The `<Router>` component wraps the application, and `<Route>` components define which component should render for a specific URL path.

```html
<script>
  import { Router, Route } from "svelte-routing";
  import Login from "./pages/Login.svelte";
  import Dashboard from "./pages/Dashboard.svelte";
</script>

<Router>
  <!-- If the URL is '/', render the Login component -->
  <Route path="/" component={Login} />
  <!-- If the URL is '/dashboard', render the Dashboard component -->
  <Route path="/dashboard" component={Dashboard} />
</Router>
```

### 2. Navigating Programmatically
Often, you need to change the route after an action completes (e.g., after a successful login). We use the `navigate` function provided by `svelte-routing`.

```html
<script>
  import { navigate } from "svelte-routing";
  import api from "../lib/api";

  async function handleSubmit() {
    // ... logic to log in ...

    // Redirect the user to the dashboard without reloading the page
    // { replace: true } means this navigation replaces the current history entry,
    // so hitting the 'Back' button won't take them back to the login page.
    navigate("/dashboard", { replace: true });
  }
</script>
```
