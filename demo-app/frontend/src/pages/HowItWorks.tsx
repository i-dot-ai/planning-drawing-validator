import React from "react";
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  SimpleGrid,
  Badge,
  Tabs,
  Code,
  Link,
  Separator,
  Flex,
} from "@chakra-ui/react";
import { Laptop, Code2, Database, ArrowRight, ShieldCheck } from "lucide-react";

const steps = [
  {
    title: "Upload & intake",
    description:
      "The frontend accepts PDF, PNG, or JPG drawings through a streamlined drag-and-drop flow. Files stream to the FastAPI backend as multipart payloads.",
  },
  {
    title: "Intelligent classification",
    description:
      "A vision-language model analyses the drawing to lock onto its type, scale, and overall composition before validation begins.",
    code: `Classification Prompt Highlights:
- Identify whether the drawing is SITE_PLAN, FLOOR_PLAN, ELEVATION, SECTION, or LOCATION_PLAN
- Return: {document_type, confidence, reasoning}`,
  },
  {
    title: "Structured requirement checks",
    description:
      "Each drawing type maps to a Pydantic schema of critical and recommended planning requirements, ensuring consistent, structured feedback.",
    code: `Floor Plan Schema:
- scale -> 1:50 or 1:100 (critical)
- floor_level -> must state level (critical)
- north_arrow -> required for external context
- room_labels -> recommended context
- dimensions -> recommended clarity`,
  },
  {
    title: "Validation response",
    description:
      "The backend responds with layered validation results: overall validity, requirement breakdowns, confidence, performance timings, and reasoning.",
  },
];

const apiPanels = [
  {
    title: "Quick start",
    content: (
      <VStack align="flex-start" gap={4}>
        <Text>
          The demo API lives at{" "}
          <Link href="http://localhost:8001" color="brand.600" target="_blank">
            http://localhost:8001
          </Link>
          . Interact via Swagger UI or ReDoc for exploratory testing.
        </Text>
        <VStack align="flex-start" gap={2} fontSize="sm" color="fg.muted">
          <HStack gap={2}>
            <Badge bg="rgba(79,134,113,0.18)" color="success.700">
              Docs
            </Badge>
            <Link
              href="http://localhost:8001/docs"
              color="brand.600"
              target="_blank"
            >
              Swagger UI — /docs
            </Link>
          </HStack>
          <HStack gap={2}>
            <Badge bg="rgba(79,134,113,0.18)" color="success.700">
              Docs
            </Badge>
            <Link
              href="http://localhost:8001/redoc"
              color="brand.600"
              target="_blank"
            >
              ReDoc — /redoc
            </Link>
          </HStack>
        </VStack>
        <Separator borderColor="rgba(145,120,100,0.24)" />
        <Text fontSize="sm" color="fg.muted">
          Authentication and rate limiting are disabled for this demo
          environment, keeping iteration frictionless.
        </Text>
      </VStack>
    ),
  },
  {
    title: "Request",
    content: (
      <VStack align="flex-start" gap={4}>
        <Text fontWeight="600">POST /validate</Text>
        <Code
          display="block"
          whiteSpace="pre"
          borderRadius="2xl"
          bg="rgba(16, 16, 16, 0.92)"
          color="green.200"
          p={4}
          fontSize="sm"
        >{`curl -X POST http://localhost:8001/validate \\
  -H "accept: application/json" \\
  -H "Content-Type: multipart/form-data" \\
  -F "file=@/path/to/drawing.pdf"`}</Code>
        <Text fontSize="sm" color="fg.muted">
          Files stream directly using multipart form data. Responses are
          returned in structured JSON.
        </Text>
      </VStack>
    ),
  },
  {
    title: "Response",
    content: (
      <VStack align="flex-start" gap={4}>
        <Code
          display="block"
          whiteSpace="pre"
          borderRadius="2xl"
          bg="rgba(16, 16, 16, 0.92)"
          color="green.200"
          p={4}
          fontSize="sm"
        >{`{
  "validity": "INVALID",
  "document_type": "FLOOR_PLAN",
  "confidence": "HIGH",
  "execution_time": 12.4,
  "reasoning": "...",
  "requirements_checked": [
    {"requirement": "scale", "status": "PASS"},
    {"requirement": "north_arrow", "status": "FAIL", "details": "Missing north arrow"},
    ...
  ]
}`}</Code>
        <Text fontSize="sm" color="fg.muted">
          The frontend reshapes these data structures into the layered feedback
          surfaces you saw earlier.
        </Text>
      </VStack>
    ),
  },
  {
    title: "Examples",
    content: (
      <VStack align="flex-start" gap={4} fontSize="sm" color="fg.muted">
        <Text>
          Repository samples live in <Code>demo-app/backend/examples</Code>.
          Pair them with our UI for end-to-end validation demos, or plug
          directly into the FastAPI endpoints.
        </Text>
        <Text>
          Feel free to script your own flows using Python's{" "}
          <Code>requests</Code> or JavaScript's <Code>fetch</Code>. The API
          remains intentionally trim for rapid iteration.
        </Text>
      </VStack>
    ),
  },
];

export const HowItWorks: React.FC = () => {
  return (
    <Box py={{ base: 10, md: 16 }}>
      <Container maxW="7xl">
        <VStack align="stretch" gap={{ base: 10, md: 14 }}>
          <Box
            position="relative"
            borderRadius={{ base: "3xl", md: "4xl" }}
            overflow="hidden"
            px={{ base: 6, md: 10 }}
            py={{ base: 10, md: 14 }}
            borderWidth="1px"
            borderColor="rgba(161, 138, 116, 0.24)"
            bg="rgba(255, 255, 255, 0.86)"
          >
            <VStack position="relative" zIndex={1} gap={6} align="flex-start">
              <Badge
                px={4}
                py={1.5}
                borderRadius="full"
                bg="rgba(79,134,113,0.18)"
                color="success.700"
                letterSpacing="0.1em"
              >
                Inside The Validator
              </Badge>
              <Heading
                size={{ base: "lg", md: "2xl" }}
                maxW="3xl"
                letterSpacing="-0.04em"
              >
                From planning drawing upload to actionable validation results.
              </Heading>
              <Text
                fontSize={{ base: "sm", md: "md" }}
                color="fg.muted"
                maxW="3xl"
              >
                The demo pairs a React frontend with a FastAPI backend and an AI
                vision-language layer. Below is the high-level architecture and
                the validation journey each drawing takes.
              </Text>
              <HStack gap={3}>
                <Badge
                  px={3}
                  py={1.5}
                  borderRadius="full"
                  bg="rgba(79,134,113,0.12)"
                  color="brand.700"
                >
                  React + Chakra UI
                </Badge>
                <Badge
                  px={3}
                  py={1.5}
                  borderRadius="full"
                  bg="rgba(218,128,94,0.14)"
                  color="brand.700"
                >
                  FastAPI + VLM
                </Badge>
                <Badge
                  px={3}
                  py={1.5}
                  borderRadius="full"
                  bg="rgba(106,175,129,0.16)"
                  color="success.700"
                >
                  Structured outputs
                </Badge>
              </HStack>
            </VStack>
          </Box>

          <SimpleGrid columns={{ base: 1, md: 3 }} gap={{ base: 6, md: 8 }}>
            {[
              {
                icon: Laptop,
                title: "Frontend studio",
                body: "React + Chakra UI deliver the interface, routing, and websocket-ready hooks.",
              },
              {
                icon: Code2,
                title: "FastAPI orchestration",
                body: "Python endpoints queue files, call the AI service, and shape structured validation responses.",
              },
              {
                icon: Database,
                title: "Model intelligence",
                body: "Vision-language models combine image and text understanding to classify and validate drawings.",
              },
            ].map((card) => (
              <Box
                key={card.title}
                borderRadius="3xl"
                borderWidth="1px"
                borderColor="rgba(47,86,71,0.18)"
                bg="rgba(255,255,255,0.94)"
                px={{ base: 5, md: 6 }}
                py={{ base: 6, md: 7 }}
              >
                <VStack align="flex-start" gap={4}>
                  <Flex
                    align="center"
                    justify="center"
                    w={12}
                    h={12}
                    borderRadius="2xl"
                    bg="rgba(79,134,113,0.12)"
                  >
                    <card.icon
                      size={24}
                      color="var(--chakra-colors-brand-600)"
                    />
                  </Flex>
                  <Heading size="md">{card.title}</Heading>
                  <Text fontSize="sm" color="fg.muted" lineHeight="1.65">
                    {card.body}
                  </Text>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>

          <VStack align="stretch" gap={{ base: 6, md: 8 }}>
            <Heading size="lg" letterSpacing="-0.02em">
              Validation pipeline
            </Heading>
            <VStack align="stretch" gap={6}>
              {steps.map((step, index) => (
                <Box
                  key={step.title}
                  borderRadius="3xl"
                  borderWidth="1px"
                  borderColor="rgba(47,86,71,0.18)"
                  bg="rgba(255,255,255,0.94)"
                  px={{ base: 5, md: 6 }}
                  py={{ base: 6, md: 8 }}
                >
                  <HStack gap={4} align="flex-start">
                    <Flex
                      align="center"
                      justify="center"
                      w={10}
                      h={10}
                      borderRadius="full"
                      bg="rgba(79,134,113,0.14)"
                    >
                      <Text fontWeight="700" color="fg.emphasis">
                        {(index + 1).toString().padStart(2, "0")}
                      </Text>
                    </Flex>
                    <VStack align="flex-start" gap={3} flex={1}>
                      <Heading size="sm">{step.title}</Heading>
                      <Text fontSize="sm" color="fg.muted" lineHeight="1.65">
                        {step.description}
                      </Text>
                      {step.code && (
                        <Code
                          display="block"
                          whiteSpace="pre"
                          borderRadius="2xl"
                          bg="rgba(16,16,16,0.9)"
                          color="green.200"
                          p={4}
                          fontSize="sm"
                        >
                          {step.code}
                        </Code>
                      )}
                    </VStack>
                  </HStack>
                </Box>
              ))}
            </VStack>
          </VStack>

          <Box>
            <Heading size="lg" letterSpacing="-0.02em" mb={4}>
              API surface
            </Heading>
            <Box
              borderRadius="3xl"
              borderWidth="1px"
              borderColor="rgba(161,138,116,0.2)"
              bg="rgba(255,255,255,0.82)"
              px={{ base: 4, md: 6 }}
              py={{ base: 5, md: 6 }}
            >
              <Tabs.Root variant="plain" defaultValue={apiPanels[0].title}>
                <Tabs.List gap={3} flexWrap="wrap">
                  {apiPanels.map((panel) => (
                    <Tabs.Trigger
                      key={panel.title}
                      value={panel.title}
                      borderRadius="full"
                      px={4}
                      py={2}
                      fontSize="sm"
                      fontWeight="600"
                      letterSpacing="0.06em"
                      textTransform="uppercase"
                      color="fg.muted"
                      _selected={{
                        bg: "rgba(218,128,94,0.16)",
                        color: "brand.700",
                      }}
                    >
                      {panel.title}
                    </Tabs.Trigger>
                  ))}
                </Tabs.List>
                <Box mt={6}>
                  {apiPanels.map((panel) => (
                    <Tabs.Content key={panel.title} value={panel.title} px={0}>
                      {panel.content}
                    </Tabs.Content>
                  ))}
                </Box>
              </Tabs.Root>
            </Box>
          </Box>

          <Box
            borderRadius="3xl"
            borderWidth="1px"
            borderColor="rgba(161,138,116,0.2)"
            bg="rgba(255,255,255,0.82)"
            px={{ base: 6, md: 8 }}
            py={{ base: 6, md: 8 }}
          >
            <VStack align="flex-start" gap={4}>
              <Heading size="md" display="flex" alignItems="center" gap={3}>
                <ShieldCheck
                  size={20}
                  color="var(--chakra-colors-success-700)"
                />
                Ready for deeper integration
              </Heading>
              <Text fontSize="sm" color="fg.muted" lineHeight="1.65">
                Extend the demo by wiring real storage, S3 uploads, or
                long-running background jobs. The FastAPI layer is intentionally
                modular—drop in queueing, authentication, or persistence as your
                production context demands, while keeping the streamlined
                frontend as your human-friendly control centre.
              </Text>
              <HStack gap={3} color="brand.600" fontWeight="600">
                <Text>Plug in more drawings</Text>
                <ArrowRight size={16} />
                <Text>Iterate on prompts</Text>
                <ArrowRight size={16} />
                <Text>Ship with confidence</Text>
              </HStack>
            </VStack>
          </Box>
        </VStack>
      </Container>
    </Box>
  );
};
