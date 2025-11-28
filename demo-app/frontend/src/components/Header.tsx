import React from "react";
import {
  Box,
  Container,
  Heading,
  Text,
  Flex,
  Button,
  HStack,
} from "@chakra-ui/react";
import { Link as RouterLink, useLocation } from "react-router-dom";
import { BookOpen } from "lucide-react";

export const Header: React.FC = () => {
  const location = useLocation();
  const navItems = [
    {
      label: "Validator",
      icon: BookOpen,
      to: "/",
    },
    {
      label: "How It Works",
      icon: BookOpen,
      to: "/how-it-works",
    },
  ];

  return (
    <Box
      as="header"
      position="sticky"
      top={0}
      zIndex={10}
      bg="bg.canvas"
      borderBottomWidth="1px"
      borderColor="rgba(79, 134, 113, 0.18)"
    >
      <Container maxW="5xl" px={{ base: 4, md: 6 }} py={{ base: 4, md: 6 }}>
        <Flex
          align={{ base: "flex-start", md: "center" }}
          justify="space-between"
          gap={{ base: 4, md: 6 }}
          wrap="wrap"
        >
          <Flex
            direction="column"
            gap={{ base: 1.5, md: 2 }}
            minW={{ base: "auto", md: "260px" }}
          >
            <Heading
              fontSize={{ base: "2xl", md: "2.5xl" }}
              letterSpacing="-0.03em"
              fontWeight="700"
              color="fg.emphasis"
            >
              Planning Drawing Validator
            </Heading>
            <Text
              fontSize={{ base: "sm", md: "md" }}
              color="fg.muted"
              maxW={{ base: "100%", md: "28rem" }}
              lineHeight="1.6"
            >
              Drop your planning drawings here to preview how they’ll be
              classified and validated before you submit the real application.
            </Text>
          </Flex>

          <HStack align="center" gap={1.5} wrap="wrap">
            {navItems.map(({ label, icon: IconComponent, to }) => {
              const isActive = location.pathname === to;
              return (
                <Button
                  key={label}
                  asChild
                  variant="ghost"
                  size="md"
                  justifyContent="flex-start"
                  px={{ base: 3, md: 4 }}
                  py={{ base: 1.5, md: 2 }}
                  borderRadius="full"
                  fontWeight="600"
                  color={isActive ? "brand.700" : "fg.muted"}
                  bg={isActive ? "rgba(79, 134, 113, 0.16)" : "transparent"}
                  _hover={{
                    bg: "rgba(79, 134, 113, 0.12)",
                    color: "brand.700",
                  }}
                  _active={{
                    bg: "rgba(79, 134, 113, 0.2)",
                  }}
                  aria-current={isActive ? "page" : undefined}
                >
                  <RouterLink to={to}>
                    <IconComponent size={16} />
                    {label}
                  </RouterLink>
                </Button>
              );
            })}
          </HStack>
        </Flex>
      </Container>
    </Box>
  );
};
