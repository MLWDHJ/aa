// 滚动时阴影效果
window.addEventListener('scroll', () => {
    const header = document.querySelector('.global-header')
    header.classList.toggle('scrolled', window.scrollY > 50)
})

function handleResponsive() {
    const header = document.querySelector('.global-header')
    if (window.innerWidth < 768) {
        header.classList.add('mobile')
    } else {
        header.classList.remove('mobile')
    }
}
window.addEventListener('resize', handleResponsive)
handleResponsive()