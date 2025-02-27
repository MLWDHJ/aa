window.addEventListener('load', function() {
    const container = document.querySelector('.carousel-container');
    const list = document.querySelector('.carousel-list');
    const dots = document.querySelector('.carousel-dots');
    const arrows = document.querySelectorAll('.arrow');
    let index = 0, timer = null;
    const originalCount = list.children.length; 

    // 动态生成圆点
    for (let i = 0; i < originalCount; i++) {
        const dot = document.createElement('li');
        dot.dataset.index = i;
        dots.appendChild(dot);
    }
    dots.children[0].className = 'active';

    // 克隆首图实现无缝滚动
    const firstClone = list.children[0].cloneNode(true);
    list.appendChild(firstClone);

  
    function handleSlide() {
        const containerWidth = container.offsetWidth;
        
        
        if (index >= originalCount) {
            list.style.transition = 'none';
            list.style.left = '0px';
            void list.offsetWidth; 
            index = 0; // 重置到第一项
            list.style.transition = 'left 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
            
            
            list.style.left = -(index * containerWidth) + 'px';
        }
        
        else if (index < 0) {
            list.style.transition = 'none';
            index = originalCount - 1;
            list.style.left = -(index * containerWidth) + 'px';
            void list.offsetWidth;
            list.style.transition = 'left 0.5s ease';
        }

        
        list.style.left = -(index * containerWidth) + 'px';
        dots.querySelectorAll('li').forEach((dot, i) => {
            
            const realIndex = index === originalCount ? 0 : index % originalCount;
            dot.className = i === realIndex ? 'active' : '';
        });
    }

    // 自动播放
    function autoPlay() {
        timer = setInterval(() => {
            index++;
            handleSlide();
        }, 3000);
    }
    autoPlay();

    // 箭头控制？？
    arrows.forEach(arrow => {
        arrow.addEventListener('click', function() {
            clearInterval(timer);
            index += this.classList.contains('left') ? -1 : 1;
            handleSlide();
            autoPlay();
        });
    });

    // 圆点点击
    dots.querySelectorAll('li').forEach((dot, i) => {
        dot.addEventListener('click', () => {
            clearInterval(timer);
            index = i;
            handleSlide();
            autoPlay();
        });
    });

    // 悬停控制
    container.addEventListener('mouseenter', () => {
        clearInterval(timer);
        arrows.forEach(arrow => arrow.style.display = 'block');
    });
    container.addEventListener('mouseleave', autoPlay);
});
//更多的跳转
document.querySelector('.more-link').addEventListener('click', function(e) {
    e.preventDefault();
    // 在这里替换实际跳转
    window.location.href = 'your-link-here.html';
});