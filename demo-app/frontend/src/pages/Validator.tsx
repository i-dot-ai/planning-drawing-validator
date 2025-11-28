import React, { useState } from "react";
import { Box } from "@chakra-ui/react";
import { DocumentUpload as DocumentUploadType } from "../types";
import { DocumentUpload } from "../components/DocumentUpload";
import { validateDocument } from "../services/api";

export const Validator: React.FC = () => {
  const [uploads, setUploads] = useState<DocumentUploadType[]>([]);

  const handleFileSelect = async (files: FileList) => {
    if (files.length === 0) return;

    // Create upload entries for all files
    const newUploads: DocumentUploadType[] = Array.from(files).map((file) => ({
      file,
      id: `${Date.now()}-${Math.random().toString(36).slice(2, 11)}`,
      status: {
        status: "uploading",
        progress: 0,
        message: "Queued for validation...",
      },
    }));

    setUploads((prev) => [...newUploads, ...prev]);

    // Process all files in parallel
    const validationPromises = newUploads.map(async (upload) => {
      try {
        // Update status to validating
        setUploads((prev) =>
          prev.map((u) =>
            u.id === upload.id
              ? {
                  ...u,
                  status: {
                    status: "validating",
                    progress: 50,
                    message: "Validating document...",
                  },
                }
              : u,
          ),
        );

        const result = await validateDocument(upload.file);

        // Update with result
        setUploads((prev) =>
          prev.map((u) =>
            u.id === upload.id
              ? {
                  ...u,
                  status: {
                    status: "complete",
                    progress: 100,
                    message: "Validation complete",
                  },
                  result,
                }
              : u,
          ),
        );

        return result;
      } catch (error) {
        // Handle error
        const errorMessage =
          error instanceof Error
            ? error.message
            : "An unexpected error occurred";

        setUploads((prev) =>
          prev.map((u) =>
            u.id === upload.id
              ? {
                  ...u,
                  status: {
                    status: "error",
                    message: errorMessage,
                  },
                }
              : u,
          ),
        );

        return null;
      }
    });

    // Wait for all validations to complete
    await Promise.all(validationPromises);
  };

  return (
    <Box py={{ base: 2, md: 3 }}>
      <DocumentUpload onFileSelect={handleFileSelect} uploads={uploads} />
    </Box>
  );
};
