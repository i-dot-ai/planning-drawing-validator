import React from "react";
import { Routes, Route } from "react-router-dom";
import { Box, Container } from "@chakra-ui/react";
import { Header } from "./components/Header";
import { Validator } from "./pages/Validator";
import { HowItWorks } from "./pages/HowItWorks";
import { OrganicBackdrop } from "./components/OrganicBackdrop";

function App() {
  return (
    <OrganicBackdrop>
      <Header />

      <Box as="main" flex={1} py={{ base: 10, md: 16 }}>
        <Container maxW="5xl" px={{ base: 4, md: 6 }}>
          <Box position="relative">
            <Routes>
              <Route path="/" element={<Validator />} />
              <Route path="/how-it-works" element={<HowItWorks />} />
            </Routes>
          </Box>
        </Container>
      </Box>
    </OrganicBackdrop>
  );
}

export default App;
