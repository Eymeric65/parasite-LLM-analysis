import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vite.dev/config/
// VITE_BASE_URL is set by the GitHub Actions deploy workflow to /<repo-name>/
// so that the build works correctly when hosted on a GitHub Pages project page.
export default defineConfig({
  plugins: [vue()],
  base: process.env.VITE_BASE_URL ?? '/',
})
