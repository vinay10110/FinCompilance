import { Box, Flex, Button, useColorModeValue } from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom'

const Navigation = () => {
  const bgColor = useColorModeValue('white', 'gray.800')
  const borderColor = useColorModeValue('gray.200', 'gray.700')

  return (
    <Box
      as="nav"
      bg={bgColor}
      borderBottom="1px"
      borderColor={borderColor}
      position="sticky"
      top={0}
      zIndex={10}
    >
      <Flex
        maxW="1200px"
        mx="auto"
        px={6}
        py={4}
        align="center"
        justify="space-between"
      >
        <RouterLink to="/">
          <Button variant="ghost" fontSize="lg" fontWeight="bold">
            RBI Compliance System
          </Button>
        </RouterLink>

        <Flex gap={4}>
          <RouterLink to="/">
            <Button variant="ghost">Dashboard</Button>
          </RouterLink>
          <Button
            as="a"
            href="/api/docs"
            target="_blank"
            variant="ghost"
          >
            API Docs
          </Button>
        </Flex>
      </Flex>
    </Box>
  )
}

export default Navigation