import { Box, Flex, Text, useColorModeValue } from '@chakra-ui/react'
import { SignedIn, SignedOut, useClerk, UserButton } from '@clerk/clerk-react'
import { Button } from '@chakra-ui/react'

const Navigation = () => {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')
  const { openSignIn } = useClerk()

  return (
    <Box
      as="nav"
      bg={bgColor}
      borderBottom="1px"
      borderColor={borderColor}
      position="fixed"
      top={0}
      left={0}
      right={0}
      zIndex={1000}
      boxShadow="sm"
    >
      <Flex
        maxW="100%"
        mx="auto"
        px={6}
        py={4}
        align="center"
        justify="space-between"
      >
        <Text fontSize="xl" fontWeight="bold">
          AI Compliance Assistant
        </Text>

        <Flex gap={4} align="center">
          <SignedIn>
            <UserButton afterSignOutUrl="/"/>
          </SignedIn>
          <SignedOut>
            <Button onClick={() => openSignIn()} colorScheme="blue">
              Sign In
            </Button>
          </SignedOut>
        </Flex>
      </Flex>
    </Box>
  )
}

export default Navigation