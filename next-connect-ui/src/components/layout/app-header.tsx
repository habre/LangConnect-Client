"use client"

import { usePathname } from "next/navigation"
import { SidebarTrigger } from "@/components/ui/sidebar"
import { Separator } from "@/components/ui/separator"
import { Breadcrumb, BreadcrumbItem, BreadcrumbLink, BreadcrumbList, BreadcrumbPage, BreadcrumbSeparator } from "@/components/ui/breadcrumb"
import { Home, Moon, Sun } from "lucide-react"
import { Button } from "../ui/button"
import { useTheme } from "next-themes"

// Navigation data structure matching sidebar
interface NavigationItem {
  name: string
  href: string
  isHome?: boolean
}

const navigationData: {
  main: NavigationItem[]
} = {
  main: [
    { name: "메인", href: "/", isHome: true },
    { name: "컬렉션", href: "/collections" },
    { name: "문서", href: "/documents" },
    { name: "검색", href: "/search" },
    { name: "API 테스터", href: "/api-tester" },
  ],
}

export function AppHeader() {
  const pathname = usePathname()

  // Generate breadcrumb items based on current path
  const generateBreadcrumb = () => {
    if (pathname === "/") {
      return [{ name: "Main", href: "/", isHome: true }]
    }

    const allItems = [
      ...navigationData.main,
    ]

    const breadcrumbItems = []

    // Find main item
    const mainItem = allItems.find(item => 
      pathname === item.href || pathname.startsWith(item.href + "/")
    )

    if (mainItem) {
      breadcrumbItems.push(mainItem)
    }

    return breadcrumbItems
  }

  const breadcrumbItems = generateBreadcrumb()
  const { theme, setTheme } = useTheme()

  return (
    <header className="flex h-14 shrink-0 items-center gap-2 border-b border-border dark:border-sidebar-border transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12 justify-between">
      <div className="flex items-center gap-2 px-4 flex-1">
        <SidebarTrigger className="-ml-1" />
        <Separator
          orientation="vertical"
          className="mr-2 data-[orientation=vertical]:h-4 bg-border dark:bg-sidebar-border"
        />
        <Breadcrumb>
          <BreadcrumbList>
            {breadcrumbItems.map((item, index) => (
              <div key={item.href} className="flex items-center">
                {index > 0 && <BreadcrumbSeparator className="text-muted-foreground dark:text-sidebar-foreground/50" />}
                <BreadcrumbItem>
                  {index === breadcrumbItems.length - 1 ? (
                    <BreadcrumbPage className="flex items-center gap-2 text-foreground dark:text-sidebar-foreground">
                      {item.isHome && <Home className="h-4 w-4" />}
                      {item.name}
                    </BreadcrumbPage>
                  ) : (
                    <BreadcrumbLink href={item.href} className="flex items-center gap-2 text-muted-foreground dark:text-sidebar-foreground/70 hover:text-foreground dark:hover:text-sidebar-foreground">
                      {item.isHome && <Home className="h-4 w-4" />}
                      {item.name}
                    </BreadcrumbLink>
                  )}
                </BreadcrumbItem>
              </div>
            ))}
          </BreadcrumbList>
        </Breadcrumb>
      </div>
      <div className="flex items-center gap-2 mr-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setTheme(theme === "light" ? "dark" : "light")}
          className="rounded-full hover:bg-accent dark:hover:bg-sidebar-accent"
        >
          <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
          <span className="sr-only">테마 변경</span>
        </Button>
      </div>
    </header>
  )
}
