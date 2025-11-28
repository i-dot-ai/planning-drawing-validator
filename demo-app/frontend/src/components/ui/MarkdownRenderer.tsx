import React from "react";
import { Box, Text } from "@chakra-ui/react";
import ReactMarkdown from "react-markdown";

interface MarkdownRendererProps {
  content: string;
  fontSize?: string | object;
  compact?: boolean;
}

/**
 * MarkdownRenderer - Consistent markdown rendering across the application
 *
 * Renders structured markdown with proper formatting for:
 * - Bold section headers (**Section:**)
 * - Bullet lists with proper indentation
 * - Inline bold text for emphasis
 * - Proper spacing between sections
 *
 * Designed to render validation reasoning with clear visual hierarchy
 */
export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({
  content,
  fontSize = { base: "md", md: "lg" },
  compact = false,
}) => {
  return (
    <Box fontSize={fontSize} color="fg.default" lineHeight="1.7">
      <ReactMarkdown
        components={{
          // Paragraph - preserve spacing
          p: ({ children }) => (
            <Text as="p" mb={compact ? 3 : 4}>
              {children}
            </Text>
          ),
          // Unordered list - proper indentation
          ul: ({ children }) => (
            <Box
              as="ul"
              pl={5}
              mb={compact ? 3 : 4}
              mt={2}
              listStyleType="disc"
            >
              {children}
            </Box>
          ),
          // List item - clear bullets
          li: ({ children }) => (
            <Text as="li" mb={2} display="list-item" pl={1}>
              {children}
            </Text>
          ),
          // Bold text - emphasis
          strong: ({ children }) => (
            <Text
              as="strong"
              fontWeight="700"
              color="fg.emphasis"
              display="inline"
            >
              {children}
            </Text>
          ),
          // Inline code
          code: ({ children }) => (
            <Text
              as="code"
              fontFamily="mono"
              fontSize="0.9em"
              bg="rgba(79, 134, 113, 0.08)"
              px={1.5}
              py={0.5}
              borderRadius="sm"
              display="inline"
            >
              {children}
            </Text>
          ),
        }}
      >
        {content}
      </ReactMarkdown>
    </Box>
  );
};
