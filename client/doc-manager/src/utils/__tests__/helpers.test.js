
// src/utils/__tests__/helpers.test.js
// Utility functions that might be used across the app

describe('File Utilities', () => {
  test('formatFileSize formats bytes correctly', () => {
    const formatFileSize = (bytes) => {
      if (bytes === 0) return '0 Bytes';
      const k = 1024;
      const sizes = ['Bytes', 'KB', 'MB', 'GB'];
      const i = Math.floor(Math.log(bytes) / Math.log(k));
      return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    };

    expect(formatFileSize(0)).toBe('0 Bytes');
    expect(formatFileSize(1024)).toBe('1 KB');
    expect(formatFileSize(1048576)).toBe('1 MB');
    expect(formatFileSize(1073741824)).toBe('1 GB');
    expect(formatFileSize(1536)).toBe('1.5 KB');
  });

  test('getMimeTypeIcon returns correct icons', () => {
    const mimeToIcon = (mimeType) => {
      if (mimeType.includes("pdf")) return "faFilePdf";
      if (mimeType.includes("image")) return "faFileImage";
      if (mimeType.includes("word")) return "faFileWord";
      if (mimeType.includes("excel") || mimeType.includes("spreadsheet")) return "faFileExcel";
      if (mimeType.includes("zip") || mimeType.includes("compressed")) return "faFileArchive";
      return "faFileAlt";
    };

    expect(mimeToIcon("application/pdf")).toBe("faFilePdf");
    expect(mimeToIcon("image/jpeg")).toBe("faFileImage");
    expect(mimeToIcon("application/vnd.openxmlformats-officedocument.wordprocessingml.document")).toBe("faFileWord");
    expect(mimeToIcon("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")).toBe("faFileExcel");
    expect(mimeToIcon("application/zip")).toBe("faFileArchive");
    expect(mimeToIcon("text/plain")).toBe("faFileAlt");
  });
});
