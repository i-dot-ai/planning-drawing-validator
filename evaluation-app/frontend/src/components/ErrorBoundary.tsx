import React, { Component, ErrorInfo, ReactNode } from "react";
import {
  Box,
  Button,
  Card,
  Code,
  Flex,
  Heading,
  HStack,
  Icon,
  Text,
  VStack,
} from "@chakra-ui/react";
import { AlertTriangle } from "lucide-react";

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

export class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null,
    errorInfo: null,
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error("ErrorBoundary caught an error:", error, errorInfo);
    this.setState({
      error,
      errorInfo,
    });
  }

  private handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  public render() {
    if (this.state.hasError) {
      return (
        <Flex minH="100vh" align="center" justify="center" bg="bg.canvas" p={6}>
          <Card.Root
            maxW="2xl"
            w="full"
            borderRadius="3xl"
            borderWidth="1px"
            borderColor="gray.200"
            boxShadow="elevated"
          >
            <Card.Header
              borderBottom="1px"
              borderColor="gray.100"
              bg="red.50"
              borderTopRadius="3xl"
            >
              <HStack gap={3}>
                <Icon as={AlertTriangle} boxSize={6} color="red.600" />
                <Heading size="md" color="red.900">
                  Something went wrong
                </Heading>
              </HStack>
            </Card.Header>
            <Card.Body p={6}>
              <VStack gap={4} align="stretch">
                <Text fontSize="sm" color="fg.muted">
                  An unexpected error occurred. Please try refreshing the page
                  or contact support if the problem persists.
                </Text>

                {this.state.error && (
                  <Box
                    borderRadius="lg"
                    bg="gray.50"
                    p={4}
                    borderWidth="1px"
                    borderColor="gray.200"
                  >
                    <Text
                      mb={2}
                      fontSize="sm"
                      fontWeight="semibold"
                      color="fg.emphasis"
                    >
                      Error Details:
                    </Text>
                    <Code
                      display="block"
                      overflowX="auto"
                      fontSize="xs"
                      color="fg.muted"
                      whiteSpace="pre-wrap"
                      bg="transparent"
                    >
                      {this.state.error.toString()}
                    </Code>
                  </Box>
                )}

                {import.meta.env.DEV && this.state.errorInfo && (
                  <Box
                    as="details"
                    borderRadius="lg"
                    bg="gray.50"
                    p={4}
                    borderWidth="1px"
                    borderColor="gray.200"
                  >
                    <Box
                      as="summary"
                      cursor="pointer"
                      fontSize="sm"
                      fontWeight="semibold"
                      color="fg.emphasis"
                    >
                      Stack Trace (Development Only)
                    </Box>
                    <Code
                      display="block"
                      mt={2}
                      overflowX="auto"
                      fontSize="xs"
                      color="fg.muted"
                      whiteSpace="pre-wrap"
                      bg="transparent"
                    >
                      {this.state.errorInfo.componentStack}
                    </Code>
                  </Box>
                )}

                <HStack gap={2}>
                  <Button
                    onClick={this.handleReset}
                    bg="gray.900"
                    color="white"
                    fontWeight="medium"
                    _hover={{ bg: "gray.800" }}
                  >
                    Try Again
                  </Button>
                  <Button
                    onClick={() => window.location.reload()}
                    variant="outline"
                    fontWeight="medium"
                  >
                    Refresh Page
                  </Button>
                </HStack>
              </VStack>
            </Card.Body>
          </Card.Root>
        </Flex>
      );
    }

    return this.props.children;
  }
}
