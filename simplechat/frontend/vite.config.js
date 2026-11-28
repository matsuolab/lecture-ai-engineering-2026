import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  build: {
    // Terraform（terraform/frontend_upload.tf）が frontend/build をアップロードする
    outDir: 'build',
    // Amplify の画面部品を含むため、JS は 1 ファイルで約 800 kB になる。警告を出さないようにする
    chunkSizeWarningLimit: 1000,
  },
});
