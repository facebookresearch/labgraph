"use client"

import classNames from "classnames";
import React, { PropsWithChildren, useState } from "react";
import Navbar from "./Navbar";
// import SideBar from "./SideBar";

import SideBar from "./SideBar";

const SideBarLayout = (props: PropsWithChildren) => {
  const [collapsed, setSidebarCollapsed] = useState(false);
  const [showSidebar, setShowSidebar] = useState(true);
  return (
    <div
      className={classNames({
        "grid bg-[#202123] min-h-screen": true,
        "grid-cols-sidebar": !collapsed,
        "grid-cols-sidebar-collapsed": collapsed,
        "transition-[grid-template-columns] duration-300 ease-in-out": true,
      })}
    >
      <SideBar
        collapsed={collapsed}
        setCollapsed={() => setSidebarCollapsed((prev) => !prev)}
        shown={showSidebar}
      ></SideBar>
    </div>
  );
};

export default SideBarLayout;

