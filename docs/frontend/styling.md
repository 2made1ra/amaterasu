# Styling and UI Architecture

This document outlines how styling is handled in the frontend project. We use a **utility-first approach** powered by Tailwind CSS.

## The Utility-First Approach: Tailwind CSS

Instead of writing custom CSS classes in separate `.css` files (e.g., creating a `.btn-primary` class and writing its styling rules), we use Tailwind CSS. Tailwind provides low-level utility classes that let you build completely custom designs directly within your HTML/Svelte markup.

### Benefits of this Approach:
1.  **No Context Switching**: You don't have to constantly switch between your `.svelte` file and a `.css` file to see or edit styles.
2.  **No Naming Conflicts**: You don't have to invent class names like `wrapper-inner-container`.
3.  **Smaller CSS Bundle**: Tailwind only includes the classes you actually use in your final build, resulting in highly optimized stylesheets.
4.  **Built-in Design System**: Tailwind provides a constrained set of spacing, colors, and typography out of the box, ensuring a consistent look and feel.

## How We Handle Styling (Examples)

All styling is applied directly via the `class` attribute in our Svelte components.

### 1. Colors and Backgrounds
We use Tailwind's color palette. For example, the primary brand color might be blue, and neutral areas might be shades of gray.
*   **Backgrounds:** `bg-gray-50` (very light gray), `bg-white`, `bg-blue-600` (primary blue).
*   **Text colors:** `text-gray-900` (dark text for headings), `text-gray-500` (subtle text), `text-white`.
*   **Borders:** `border-gray-300`, `border-blue-500`.

### 2. Spacing and Layout
Spacing (margin and padding) uses a proportional scale (where `1` usually equals `0.25rem` or `4px`).
*   **Padding:** `p-4` (padding of 1rem/16px all around), `px-4` (horizontal padding), `py-2` (vertical padding).
*   **Margin:** `mb-4` (margin-bottom of 1rem), `mt-6` (margin-top of 1.5rem).

### 3. Flexbox and Grid
Layouts are predominantly built using Flexbox utilities.
*   `flex`: Turns the element into a flex container.
*   `flex-col`: Stacks children vertically.
*   `justify-center`, `justify-between`: Aligns items along the main axis.
*   `items-center`: Aligns items along the cross axis.

### 4. Typography
Font sizes and weights are controlled via utilities.
*   `text-sm` (small text), `text-lg` (large text), `text-3xl` (very large heading).
*   `font-medium`, `font-semibold`, `font-extrabold`.

### 5. Interactive States (Hover, Focus)
Interactive states are styled using prefixes.
*   **Hover:** `hover:bg-blue-700` (changes background color when hovered), `hover:text-red-800`.
*   **Focus:** `focus:outline-none focus:ring-2 focus:ring-blue-500` (adds a blue ring around an input when focused).
*   **Disabled:** `disabled:bg-gray-400` (changes appearance when a button is disabled).

### Example Breakdown

Here is a typical button from our application:

```html
<button class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:bg-gray-400">
  Submit
</button>
```

*   `w-full flex justify-center`: Takes up full width and centers the content using Flexbox.
*   `py-2 px-4`: Vertical padding 8px, horizontal padding 16px.
*   `rounded-md shadow-sm`: Medium rounded corners and a small shadow.
*   `text-sm font-medium text-white bg-blue-600`: Small, bold, white text on a blue background.
*   `hover:bg-blue-700`: Darker blue on hover.
*   `focus:...`: Accessibility styles for keyboard navigation.

## Global Styles

While 99% of styling is done via utility classes, there is a small `src/app.css` file. This file is primarily used to inject the base Tailwind directives (`@tailwind base;`, `@tailwind components;`, `@tailwind utilities;`) and might contain a few global overrides (like setting `html, body` to take up 100% height), but custom CSS classes should be avoided here.
