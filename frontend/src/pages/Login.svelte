<script>
  import { navigate } from "svelte-routing";
  import api from "../lib/api";

  let username = "";
  let password = "";
  let isRegistering = false;
  let error = "";

  async function handleSubmit() {
    error = "";
    try {
      if (isRegistering) {
        await api.post("/auth/register", { username, password });
        isRegistering = false;
        alert("Registration successful. Please login.");
      } else {
        const formData = new URLSearchParams();
        formData.append("username", username);
        formData.append("password", password);
        const res = await api.post("/auth/login", formData, {
          headers: { "Content-Type": "application/x-www-form-urlencoded" }
        });
        localStorage.setItem("token", res.data.access_token);
        navigate("/dashboard", { replace: true });
      }
    } catch (err) {
      error = err.response?.data?.detail || "An error occurred";
    }
  }
</script>

<div class="min-h-screen bg-gray-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
  <div class="sm:mx-auto sm:w-full sm:max-w-md">
    <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
      {isRegistering ? "Create an account" : "Sign in to your account"}
    </h2>
  </div>

  <div class="mt-8 sm:mx-auto sm:w-full sm:max-w-md">
    <div class="bg-white py-8 px-4 shadow sm:rounded-lg sm:px-10">
      {#if error}
        <div class="mb-4 text-red-600 text-sm">{error}</div>
      {/if}
      <form class="space-y-6" on:submit|preventDefault={handleSubmit}>
        <div>
          <label for="username" class="block text-sm font-medium text-gray-700">Username</label>
          <div class="mt-1">
            <input id="username" bind:value={username} type="text" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
          </div>
        </div>

        <div>
          <label for="password" class="block text-sm font-medium text-gray-700">Password</label>
          <div class="mt-1">
            <input id="password" bind:value={password} type="password" required class="appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm" />
          </div>
        </div>

        <div>
          <button type="submit" class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
            {isRegistering ? "Register" : "Sign in"}
          </button>
        </div>
      </form>
      <div class="mt-6 text-center">
        <button type="button" class="text-sm text-blue-600 hover:text-blue-500" on:click={() => isRegistering = !isRegistering}>
          {isRegistering ? "Already have an account? Sign in" : "Need an account? Register"}
        </button>
      </div>
    </div>
  </div>
</div>
